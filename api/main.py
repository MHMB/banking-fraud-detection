"""AML path-analysis API over the Neo4j banking graph.

Run:  uvicorn main:app --app-dir api --port 8000      (docs at /docs)
Env:  NEO4J_URI (bolt://localhost:7687), NEO4J_USER (neo4j), NEO4J_PASSWORD (password123)
"""
import os

from fastapi import FastAPI, HTTPException, Query
from neo4j import GraphDatabase
from pydantic import BaseModel, Field

import graph

app = FastAPI(title="Banking AML path analysis")
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password123")),
)


def load_transfers() -> list:
    # ponytail: reads every transaction per request; cache or push the search
    # into Cypher once the graph no longer fits comfortably in memory.
    rows, _, _ = driver.execute_query("""
        MATCH (t:Transaction)
        RETURN t.transaction_id AS id, t.date AS date, t.time AS time,
               t.sender_sheba AS src, t.receiver_sheba AS dst, t.amount AS amount,
               t.type AS type, t.channel AS channel,
               coalesce(t.description, '') AS description, t.scenario AS scenario
    """)
    return [graph.Tx(**r.data()) for r in rows]


def require_accounts(shebas: list):
    rows, _, _ = driver.execute_query(
        "MATCH (a:Account) WHERE a.sheba IN $shebas RETURN collect(a.sheba) AS found", shebas=shebas)
    missing = sorted(set(shebas) - set(rows[0]["found"]))
    if missing:
        raise HTTPException(404, f"Unknown sheba: {', '.join(missing)}")


@app.get("/health")
def health():
    driver.verify_connectivity()
    return {"status": "ok"}


@app.get("/shebas/{sheba}/scatter-gather")
def scatter_gather(
    sheba: str,
    min_branches: int = Query(2, ge=2, description="Minimum separate branches between source and target"),
    max_hops: int = Query(3, ge=1, le=6, description="Maximum intermediaries per branch"),
    window_days: int = Query(30, ge=1, description="Whole pattern must fit in this many days"),
    min_ratio: float = Query(0.8, gt=0, le=1, description="Each account forwards at least this share of what it received"),
):
    """Did this sheba take part in a scatter-then-gather pattern, and in which role
    (source, target, intermediary)? Returns every branch with its transactions."""
    require_accounts([sheba])
    patterns = graph.scatter_gather_for(load_transfers(), sheba, min_branches=min_branches,
                                        max_hops=max_hops, window_days=window_days, min_ratio=min_ratio)
    return {"sheba": sheba, "involved": bool(patterns), "patterns": patterns}


class RelationshipRequest(BaseModel):
    shebas: list[str] = Field(min_length=2, max_length=50)


@app.post("/relationships")
def relationships(body: RelationshipRequest):
    """For every pair of the given shebas: is there a time-ordered money path between
    them (either direction, any number of intermediaries), and do they share an owner?"""
    shebas = list(dict.fromkeys(body.shebas))
    require_accounts(shebas)
    pairs = graph.relationships(load_transfers(), shebas)
    rows, _, _ = driver.execute_query("""
        MATCH (a:Account)<-[:OWNS_ACCOUNT]-(c:Customer)-[:OWNS_ACCOUNT]->(b:Account)
        WHERE a.sheba IN $shebas AND b.sheba IN $shebas AND a.sheba <> b.sheba
        RETURN a.sheba AS a, b.sheba AS b, collect(c.shab_id) AS owners
    """, shebas=shebas)
    owners = {(r["a"], r["b"]): r["owners"] for r in rows}
    for p in pairs:
        p["shared_owners"] = owners.get((p["a"], p["b"]), [])
        p["related"] = p["related"] or bool(p["shared_owners"])
    return {"pairs": pairs}
