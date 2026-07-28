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
| Sheba (IBAN) | 26 characters, `IR` + mod-97 check digits, real Iranian bank codes |
| National ID | 10 digits with a valid check digit |
| SHAHAB ID | Generated per customer |
| Dates | Solar Hijri (`YYYYMMDD`) |
| Field names | Persian, matching real bank report columns (30 fields) |

### Scale

- **180** accounts · **150** customers · **10** Iranian banks
- **610** transactions across **8** scenarios
- Reproducible: every script takes `--seed` (default `42`)

---

## The eight fraud scenarios

Each scenario mixes fraudulent transactions with legitimate ones, so the fraud is not
trivially visible — it has to be found by analysis. Patterns are based on
[FATF](https://www.fatf-gafi.org/) typologies.

| # | Scenario | Pattern | Tx | Volume (IRR) |
|---|---|---|---|---|
| 01 | Simple Layering | `A→B→C→D` | 70 | 748M |
| 02 | Structuring (Smurfing) | Below reporting threshold | 86 | 1.98B |
| 03 | Shell Company Network | `A→B→C→A` | 51 | 3.17B |
| 04 | Terrorist Financing | Many→One→Foreign | 122 | 1.27B |
| 05 | Account Takeover | Behaviour change | 56 | 1.55B |
| 06 | Trade-Based ML | Over-invoicing | 70 | 9.74B |
| 07 | Insider Fraud | Employee abuse | 51 | 1.73B |
| 08 | Circular Payments | 18-hop circle | 104 | 13.34B |

---

## Graph model

**Nodes:** `Bank` (10) · `Customer` (150) · `Account` (180) · `Transaction` (610)

**Relationships:**

```
(Customer)-[:OWNS_ACCOUNT]->(Account)
(Account)-[:BELONGS_TO_BANK]->(Bank)
(Account)-[:SENT]->(Transaction)
(Transaction)-[:RECEIVED]->(Account)
```

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
python generate_transactions.py --scenario 01 --accounts accounts_master.csv --output scenario_01
```

The generators use only the Python standard library — no dependencies.

---

## Repository layout

| Path | Contents |
|---|---|
| `generate_accounts.py` | Account/customer master-data generator |
| `generate_transactions.py` | Per-scenario transaction generator |
| `create_readmes.py` | Generates per-scenario documentation |
| `accounts_master.csv` | 180 accounts, 30 Persian columns |
| `scenario_01..08/` | `transactions.csv` + `README.md` per scenario |
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
| Total accounts / customers / transactions | 180 / 150 / 610 |
| Null sender or receiver Sheba | 0 |
| Duplicate transactions | 0 |
| Negative amounts | 0 |
| Transactions referencing unknown accounts | 0 |
| Sheba mod-97 check digits valid | 180 / 180 |
| National ID check digits valid | all |

---

## References

- [FATF 40 Recommendations](https://www.fatf-gafi.org/publications/fatf-standards/)
- [FATF Typologies Reports](https://www.fatf-gafi.org/publications/typologies/)
- [Central Bank of Iran](https://www.cbi.ir/)
- [Sheba / IBAN structure — Iran](https://www.ibantest.com/en/iban-structure/iran)
