# Iranian Banking Fraud Detection — Synthetic Data & Neo4j Graph Analysis

Simulation of eight bank-fraud typologies on **fully synthetic** Iranian banking data,
loaded into a Neo4j graph database and analysed with Cypher.

> **All data in this repository is synthetic and programmatically generated.**
> No real customer, account, or transaction data is used anywhere in this project.

**Author:** Mohammad Motiebirjandi
**Report:** [`fraud_detection_report.pdf`](fraud_detection_report.pdf) (Persian, RTL)

---

## What this project does

Real banking data cannot be used for fraud-detection research for privacy reasons.
This project generates realistic substitute data that respects the actual rules of the
Iranian banking system, plants known fraud patterns inside it, and then demonstrates
how a graph database detects those patterns.

### Data realism

| Field | Rule enforced |
|---|---|
| Sheba (IBAN) | 26 characters, `IR` + mod-97 check digits, real CBI bank identifiers (017 Melli, 012 Mellat, …) |
| National ID | Individuals: 10 digits with check digit · Companies: 11-digit شناسه ملی with check digit |
| SHAHAB ID | 16 digits, per customer |
| Branches | Each bank has its own branches; accounts open at their bank's branch |
| Dates | Solar Hijri (`YYYYMMDD`), real month lengths and leap years; no branch/PAYA/SATNA on Friday |
| Transaction types | واریز نقدی, برداشت نقدی, انتقال داخلی, پایا, ساتنا (≥ 150M); cash has no counterparty |
| Field names | Persian, matching real bank report columns (30 fields) |

### Scale

- **180** accounts · **150** customers · **10** Iranian banks
- **1,499** transactions across **8** scenarios, of which **212** are planted fraud
- Reproducible: every script takes `--seed` (default `42`)

---

## The eight fraud scenarios

Each scenario plants one typology inside realistic background activity (salaries,
purchases, rent, cash, B2B invoices, large personal transfers). The fraud is deliberately
hidden: neutral descriptions, amounts that overlap legitimate traffic, and fraud actors
that also do normal business — it has to be found by analysis. Patterns are based on
[FATF](https://www.fatf-gafi.org/) typologies.

| # | Scenario | Pattern | Tx | Planted | Period |
|---|---|---|---|---|---|
| 01 | Simple Layering | cash→`A→B→C→D`→cash, ×3 | 135 | 15 | 35 days |
| 02 | Structuring (Smurfing) | 15 cash deposits < 50M → aggregator | 181 | 31 | 35 days |
| 03 | Shell Company Network | `A→B→C→A`, ×4 | 132 | 12 | 45 days |
| 04 | Terrorist Financing | 50 donors → charity → NGO → foreign | 354 | 104 | 68 days |
| 05 | Account Takeover | 6-month baseline, then night drain | 181 | 4 | 6 months |
| 06 | Trade-Based ML | importer → broker (−15%) → foreign, ×5 | 160 | 10 | 3 months |
| 07 | Insider Fraud | dormant same-branch accounts → mules → cash | 132 | 12 | 35 days |
| 08 | Circular Payments | 18-hop ring back to origin + side paths | 224 | 24 | 55 days |

Ground truth lives in `scenario_NN/ground_truth.csv` (`transaction_id, role`). It is **not**
imported into Neo4j, so detection queries cannot cheat; use it only to score results.

---

## Graph model

**Nodes:** `Bank` (10) · `Customer` (150: `Person` 120 incl. `ForeignNational` 9, `Company` 30) · `Account` (180) · `Transaction` (1,499)

**Relationships:**

```
(Customer)-[:OWNS_ACCOUNT]->(Account)
(Account)-[:BELONGS_TO_BANK]->(Bank)
(Account)-[:SENT]->(Transaction)
(Transaction)-[:RECEIVED]->(Account)
```

Cash deposits have only `RECEIVED`, cash withdrawals only `SENT`.

Every scenario has a matching Cypher detection query — see the report.

---

## Quick start

Requires Docker and Python 3.10+.

```bash
bash setup.sh
```

This starts Neo4j 5.26.2 in Docker, waits for it to be healthy, and imports the full
dataset. Then open the Neo4j Browser at <http://localhost:7474>.

To use a password other than the development default:

```bash
NEO4J_PASSWORD=your-password docker compose up -d
```

> **Note:** `password123` is a development default for a container bound to localhost.
> Change it before exposing Neo4j on any network.

### Regenerating the data

```bash
python generate_accounts.py --accounts 180 --customers 150 --output accounts_master.csv
python generate_transactions.py --scenario all --accounts accounts_master.csv
python create_readmes.py --all
```

After regenerating, reset Neo4j so old transactions are not kept:
`docker compose down -v && bash setup.sh`, then `python output/generate_all.py` for the charts.

The generators use only the Python standard library — no dependencies.

---

## Repository layout

| Path | Contents |
|---|---|
| `generate_accounts.py` | Account/customer master-data generator |
| `generate_transactions.py` | Per-scenario transaction generator |
| `create_readmes.py` | Generates per-scenario documentation |
| `accounts_master.csv` | 180 accounts, 30 Persian columns |
| `scenario_01..08/` | `transactions.csv` + `ground_truth.csv` + `README.md` per scenario |
| `import_data.cypher` | Neo4j import script |
| `verify_neo4j.py` | Post-import data validation |
| `output/` | Generated analysis charts and stats per scenario |
| `report_assets/` | Figures used in the report (graphs, distributions, timelines) |
| `neo4j_images/` | Neo4j Browser graph screenshots |
| `fraud_detection_report.{pdf,docx,md}` | Full technical report (Persian, RTL) |
| `SUMMARY.md` | Detailed technical specification |
| `DOCKER_SETUP.md` | Environment setup notes |

---

## Data validation

| Check | Result |
|---|---|
| Total accounts / customers / transactions | 180 / 150 / 1,499 |
| Transactions with neither sender nor receiver | 0 (cash tx have exactly one side) |
| Duplicate transaction IDs (across all scenarios) | 0 |
| Negative / zero amounts | 0 / 0 |
| Transactions referencing unknown accounts | 0 |
| Invalid Solar Hijri dates | 0 |
| Sheba mod-97 check digits valid | 180 / 180 |
| National ID / legal-entity ID check digits valid | all |

---

## References

- [FATF 40 Recommendations](https://www.fatf-gafi.org/publications/fatf-standards/)
- [FATF Typologies Reports](https://www.fatf-gafi.org/publications/typologies/)
- [Central Bank of Iran](https://www.cbi.ir/)
- [Sheba / IBAN structure — Iran](https://www.ibantest.com/en/iban-structure/iran)
