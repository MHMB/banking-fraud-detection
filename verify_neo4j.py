#!/usr/bin/env python3
"""
Neo4j Data Verification Script
Run this script to verify your Neo4j database has all the data imported correctly.
Usage: python3 verify_neo4j.py
Requirements: pip install neo4j
"""

from neo4j import GraphDatabase
import sys

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password123")

QUERIES = [
    ("Node counts by type",
     "MATCH (n) RETURN labels(n)[0] AS NodeType, count(n) AS Count ORDER BY Count DESC"),

    ("Relationship counts",
     "MATCH ()-[r]->() RETURN type(r) AS RelType, count(r) AS Count ORDER BY Count DESC"),

    ("Transactions per scenario",
     "MATCH (tx:Transaction) RETURN tx.scenario AS Scenario, count(tx) AS Count ORDER BY Scenario"),

    ("Orphaned transactions (should be 0)",
     "MATCH (tx:Transaction) WHERE NOT (tx)<-[:SENT]-() OR NOT (tx)-[:RECEIVED]->() RETURN count(tx) AS orphaned"),

    ("Accounts without bank (should be 0 for master accounts)",
     "MATCH (a:Account) WHERE a.in_master = true AND NOT (a)-[:BELONGS_TO_BANK]->() RETURN count(a) AS no_bank"),

    ("Placeholder accounts (not in master)",
     "MATCH (a:Account) WHERE a.in_master = false RETURN count(a) AS placeholder_count"),

    ("Scenario 01 - Layering chains",
     """MATCH (a1:Account)-[:SENT]->(tx1:Transaction)-[:RECEIVED]->(a2:Account)
        WHERE tx1.scenario = 'scenario_01' AND tx1.amount > 40000000
        RETURN a1.sheba AS sender, a2.sheba AS receiver, tx1.amount AS amount
        ORDER BY tx1.amount DESC LIMIT 5"""),

    ("Scenario 02 - Below threshold transactions",
     """MATCH (a:Account)-[:SENT]->(tx:Transaction)
        WHERE tx.scenario = 'scenario_02' AND tx.amount >= 40000000 AND tx.amount <= 50000000
        RETURN count(tx) AS near_threshold_count, avg(tx.amount) AS avg_amount"""),

    ("Scenario 03 - Circular flows",
     """MATCH (a1:Account)-[:SENT]->(tx1:Transaction {scenario:'scenario_03'})-[:RECEIVED]->(a2:Account)
        -[:SENT]->(tx2:Transaction {scenario:'scenario_03'})-[:RECEIVED]->(a3:Account)
        WHERE a1.sheba = a3.sheba
        RETURN a1.sheba AS circular_account, count(*) AS cycles"""),

    ("Scenario 04 - Hub detection (aggregators)",
     """MATCH (donor:Account)-[:SENT]->(tx:Transaction {scenario:'scenario_04'})-[:RECEIVED]->(hub:Account)
        WITH hub, count(DISTINCT donor) AS donors, sum(tx.amount) AS total
        WHERE donors > 5
        RETURN hub.sheba, donors, total ORDER BY donors DESC"""),

    ("Scenario 08 - Most connected nodes",
     """MATCH (a:Account)-[:SENT]->(tx:Transaction {scenario:'scenario_08'})
        WITH a, count(tx) AS out_degree
        ORDER BY out_degree DESC LIMIT 5
        RETURN a.sheba, out_degree"""),
]

def main():
    print("=" * 60)
    print("Neo4j Data Verification - Banking Fraud Detection")
    print("=" * 60)

    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        driver.verify_connectivity()
        print(f"\n✅ Connected to Neo4j at {URI}\n")
    except Exception as e:
        print(f"\n❌ Failed to connect: {e}")
        sys.exit(1)

    with driver.session() as session:
        for title, query in QUERIES:
            print(f"\n--- {title} ---")
            try:
                result = session.run(query)
                records = list(result)
                if not records:
                    print("  (no results)")
                for rec in records:
                    print(f"  {dict(rec)}")
            except Exception as e:
                print(f"  ERROR: {e}")

    driver.close()
    print("\n" + "=" * 60)
    print("Verification complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
