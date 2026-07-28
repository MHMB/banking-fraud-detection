"""Helper to query Neo4j HTTP API and return results as dicts."""
import json
import urllib.request
import urllib.error

NEO4J_URL = "http://localhost:7474/db/neo4j/tx/commit"
AUTH = ("neo4j", "password123")

def query(cypher, params=None):
    """Run a Cypher query and return list of row dicts."""
    body = {"statements": [{"statement": cypher}]}
    if params:
        body["statements"][0]["parameters"] = params
    data = json.dumps(body).encode("utf-8")

    import base64
    creds = base64.b64encode(f"{AUTH[0]}:{AUTH[1]}".encode()).decode()

    req = urllib.request.Request(
        NEO4J_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {creds}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())

    if result.get("errors"):
        raise RuntimeError(result["errors"])

    rows = []
    for res in result["results"]:
        cols = res["columns"]
        for d in res["data"]:
            rows.append(dict(zip(cols, d["row"])))
    return rows
