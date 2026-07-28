# Banking Fraud Detection — Iranian Banking Fraud Scenario Simulation

Simulation of **8 common fraud scenarios in the Iranian banking system**, built with fully synthetic but realistic data, and analyzed with the **Neo4j** graph database.

> Prepared by Mohammad Motiebirjandi. All data is programmatically generated and synthetic — no real customer or bank data is used.

## Overview

- **180 bank accounts**, **150 customers**, across **10 Iranian banks**
- Valid Sheba (IBAN) numbers with mod-97 check digits, valid Iranian national IDs
- **610 transactions** across 8 fraud scenarios, each mixing fraudulent and legitimate activity
- Fraud patterns follow **FATF typologies**
- Data imported into **Neo4j 5.x** (via Docker) with Cypher detection queries for each scenario

## Fraud Scenarios

| # | Scenario | Pattern |
|---|----------|---------|
| 01 | Simple Layering | A→B→C→D rapid movement |
| 02 | Structuring (Smurfing) | Deposits just below the 50M IRR reporting threshold |
| 03 | Shell Company Network | Circular corporate payments A→B→C→A |
| 04 | Terrorist Financing | Many small donations → charity → foreign entity |
| 05 | Account Takeover | Sudden behavior change on a legitimate account |
| 06 | Trade-Based Money Laundering | Over-invoicing through a free-zone intermediary |
| 07 | Insider Fraud | Bank employee abusing dormant/elderly accounts |
| 08 | Circular Payments | 18-hop circular network with commission decay |

Each `scenario_XX/` folder contains the transaction data (`transactions.csv`) and a README with the fraud indicators and analysis guidance.

## Repository Structure

```
├── generate_accounts.py       # Generates account/customer master data (valid Sheba & national IDs)
├── generate_transactions.py   # Generates transactions for the 8 fraud scenarios
├── create_readmes.py          # Auto-generates per-scenario documentation
├── verify_neo4j.py            # Verifies the Neo4j import
├── import_data.cypher         # Cypher script to load all data into Neo4j
├── docker-compose.yml         # Neo4j container setup
├── setup.sh                   # One-shot environment setup
├── accounts_master.csv        # Master data: 180 accounts / 150 customers (UTF-8-sig, Persian)
├── scenario_01 … scenario_08/ # Per-scenario transactions + README
├── output/                    # Analysis & visualization scripts (charts, graphs, timelines)
├── SUMMARY.md                 # Full English technical summary
├── DOCKER_SETUP.md            # Neo4j/Docker setup guide
└── fraud_detection_report.md  # Full technical report (Persian)
```

## Quick Start

```bash
# 1. Start Neo4j
docker compose up -d

# 2. (Re)generate data if needed — reproducible with --seed 42
python generate_accounts.py --accounts 200 --customers 160 --output accounts_master.csv
for s in {01..08}; do
    python generate_transactions.py --scenario $s --accounts accounts_master.csv --output "scenario_$s"
done

# 3. Import into Neo4j
# run import_data.cypher in Neo4j Browser or cypher-shell, then:
python verify_neo4j.py

# 4. Generate analysis charts
python output/generate_all.py
```

## Graph Model

Nodes: `Bank`, `Customer`, `Account`, `Transaction`
Relationships: `(Account)-[:BELONGS_TO_BANK]->(Bank)`, `(Customer)-[:OWNS_ACCOUNT]->(Account)`, `(Account)-[:SENT]->(Transaction)-[:RECEIVED]->(Account)`

Detection Cypher queries for every scenario are included in the report (`fraud_detection_report.md`).

## Notes

- All CSVs use **UTF-8-sig** encoding (Persian text).
- Dates are in **Solar Hijri** format (YYYYMMDD).
- Scripts use only the Python standard library (Python 3.7+); analysis scripts in `output/` additionally use pandas, networkx, and matplotlib.
- Report images/screenshots are not committed to keep the repo light; see the generated report PDF/DOCX.
