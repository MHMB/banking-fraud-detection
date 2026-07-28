# Neo4j Graph Capture — Complete Prompt for Claude in Chrome

Copy and paste this entire prompt into Claude in Chrome extension.

---

## TASK

I need you to capture screenshots from my Neo4j Browser dashboard. Neo4j is running locally. You will run **9 Cypher queries** (one overview + eight fraud scenarios), wait for each graph to render, and take a screenshot. Save each screenshot to a specific file path on my computer.

## CONNECTION DETAILS

- **URL:** `http://localhost:7474/browser/`
- **Username:** `neo4j`
- **Password:** `password123`
- **Bolt URL:** `bolt://localhost:7687`

## STEP-BY-STEP INSTRUCTIONS

### Step 0: Open Neo4j Browser and Log In

1. Navigate to `http://localhost:7474/browser/`
2. If prompted to connect, use:
   - Connect URL: `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: `password123`
3. Click "Connect"
4. Wait until the Neo4j Browser interface is fully loaded

### Step 1: Resize Window

Resize the browser window to **1920×1080** for consistent, high-resolution captures.

### Step 2: Run Each Query Below

For **each query** below, do the following:

1. **Clear** the current frame (click the X or use `:clear`)
2. **Paste** the Cypher query into the editor bar at the top
3. **Run** the query (click the Play button or press Ctrl+Enter)
4. **Wait 3-5 seconds** for the graph to fully render and stabilize
5. If the result is a graph visualization, **let the force-directed layout settle** (nodes stop moving)
6. **Take a screenshot** and save it to the specified file path

---

## THE 9 QUERIES

---

### Query 0: Full Database Overview
**Save to:** `~/milit-service/banking_analysis/report_assets/overview/neo4j_full_graph.png`

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 150
```

*This gives an overview of the entire graph model. After it renders, zoom out a bit so all nodes are visible.*

---

### Query 1: Scenario 01 — Simple Layering (A→B→C→D)
**Save to:** `~/milit-service/banking_analysis/report_assets/scenario_01/neo4j_graph.png`

```cypher
MATCH path=(a1:Account)-[:SENT]->(tx1:Transaction)-[:RECEIVED]->(a2:Account)-[:SENT]->(tx2:Transaction)-[:RECEIVED]->(a3:Account)
WHERE tx1.scenario = 'scenario_01' AND tx2.scenario = 'scenario_01'
  AND tx1.amount >= 40000000
RETURN path
LIMIT 50
```

---

### Query 2: Scenario 02 — Structuring / Smurfing
**Save to:** `~/milit-service/banking_analysis/report_assets/scenario_02/neo4j_graph.png`

```cypher
MATCH (a:Account)-[:SENT]->(tx:Transaction)-[:RECEIVED]->(b:Account)
WHERE tx.scenario = 'scenario_02'
  AND tx.amount >= 40000000 AND tx.amount <= 50000000
RETURN a, tx, b
LIMIT 60
```

---

### Query 3: Scenario 03 — Shell Company Network (Circular A→B→C→A)
**Save to:** `~/milit-service/banking_analysis/report_assets/scenario_03/neo4j_graph.png`

```cypher
MATCH path=(a1:Account)-[:SENT]->(tx1:Transaction {scenario:'scenario_03'})-[:RECEIVED]->(a2:Account)-[:SENT]->(tx2:Transaction {scenario:'scenario_03'})-[:RECEIVED]->(a3:Account)-[:SENT]->(tx3:Transaction {scenario:'scenario_03'})-[:RECEIVED]->(a4:Account)
WHERE a1.sheba = a4.sheba OR tx1.amount >= 100000000
RETURN path
LIMIT 50
```

---

### Query 4: Scenario 04 — Terrorist Financing (Many→One→Foreign)
**Save to:** `~/milit-service/banking_analysis/report_assets/scenario_04/neo4j_graph.png`

```cypher
MATCH (donor:Account)-[:SENT]->(tx:Transaction {scenario:'scenario_04'})-[:RECEIVED]->(hub:Account)
WITH hub, collect(DISTINCT donor) AS donors, collect(tx) AS txns
WHERE size(donors) >= 3
UNWIND donors AS d
UNWIND txns AS t
RETURN d, t, hub
LIMIT 80
```

---

### Query 5: Scenario 05 — Account Takeover
**Save to:** `~/milit-service/banking_analysis/report_assets/scenario_05/neo4j_graph.png`

```cypher
MATCH (a:Account)-[:SENT]->(tx:Transaction {scenario:'scenario_05'})-[:RECEIVED]->(b:Account)
WITH a, tx, b
ORDER BY tx.amount DESC
RETURN a, tx, b
LIMIT 50
```

---

### Query 6: Scenario 06 — Trade-Based Money Laundering
**Save to:** `~/milit-service/banking_analysis/report_assets/scenario_06/neo4j_graph.png`

```cypher
MATCH (sender:Account)-[:SENT]->(tx:Transaction {scenario:'scenario_06'})-[:RECEIVED]->(receiver:Account)
WHERE tx.amount > 200000000
RETURN sender, tx, receiver
LIMIT 50
```

---

### Query 7: Scenario 07 — Insider Fraud (Employee Abuse)
**Save to:** `~/milit-service/banking_analysis/report_assets/scenario_07/neo4j_graph.png`

```cypher
MATCH (victim:Account)-[:SENT]->(tx:Transaction {scenario:'scenario_07'})-[:RECEIVED]->(beneficiary:Account)
WHERE victim.branch_code = '5692412' OR tx.amount >= 50000000
RETURN victim, tx, beneficiary
LIMIT 50
```

---

### Query 8: Scenario 08 — Circular Payments (18-Hop Network)
**Save to:** `~/milit-service/banking_analysis/report_assets/scenario_08/neo4j_graph.png`

```cypher
MATCH path = (a:Account)-[:SENT]->(:Transaction {scenario:'scenario_08'})-[:RECEIVED]->(b:Account)
WITH a, b, count(*) AS tx_count
WHERE tx_count > 1
MATCH p = (a)-[:SENT]->(tx:Transaction {scenario:'scenario_08'})-[:RECEIVED]->(b)
RETURN p
LIMIT 80
```

---

## IMPORTANT NOTES

- **Wait for graph stabilization:** After each query runs, the nodes will bounce around for a few seconds. Wait until they stop moving before taking the screenshot.
- **Graph view, not table view:** Make sure the results are displayed as a **Graph** (not Table or Text). Click the graph icon in the result frame if needed.
- **Zoom to fit:** If nodes are too small or too spread out, use the "Zoom to Fit" button (the square icon in the bottom-right of the graph frame) before screenshotting.
- **Dark mode preferred:** If Neo4j is in light mode, that's fine too — but dark mode looks better for the report.
- **File paths:** Save screenshots to the exact paths specified. The `~` refers to `/Users/mhmb/` on this Mac.
- **Resolution:** Take screenshots at the highest resolution possible.

## AFTER ALL CAPTURES

Once all 9 screenshots are saved, please list the files you saved and confirm each one was captured successfully.
