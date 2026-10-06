#!/usr/bin/env python3
"""
Generate README.md files for each fraud detection scenario
Creates scenario documentation with fraud indicators and statistics
"""

import csv
import os


def stats(transactions_file: str) -> str:
    """Counts straight from the generated files."""
    with open(transactions_file, encoding='utf-8-sig') as f:
        tx = list(csv.DictReader(f))
    with open(os.path.join(os.path.dirname(transactions_file), 'ground_truth.csv'), encoding='utf-8-sig') as f:
        planted = sum(1 for _ in csv.DictReader(f))
    return (f"- **Total Transactions:** {len(tx)}\n"
            f"- **Planted Fraud Transactions:** {planted}\n"
            f"- **Background (legitimate) Transactions:** {len(tx) - planted}\n"
            f"- **Period:** {tx[0]['date']} – {tx[-1]['date']}")

SCENARIO_INFO = {
    "01": {
        "title": "Simple Layering (Money Laundering)",
        "description": """
**Pattern:** cash in → A → B → C → D → cash out, repeated 3 times

Cash is placed just below the reporting threshold into a recently opened account and
pushed through three more individual accounts within ~4 days, losing 0.5M per hop,
then withdrawn in cash.

**Planted (roles in ground_truth.csv):**
- `placement`: cash deposits of 45M, 48.5M, 42M into A (branch, early morning)
- `layering`: A→B→C→D, one hop per business day, −0.5M per hop
- `integration`: D withdraws the amount minus 5M in cash

**How it is hidden:**
- Legitimate cash deposits and salaries of similar size (up to ~49.5M)
- A, B, C, D also send/receive ordinary payments
- Neutral or empty descriptions

**Indicators:** sub-threshold cash followed by fast pass-through; decreasing amounts; new first account.
""",
    },
    "02": {
        "title": "Structuring (Smurfing)",
        "description": """
**Pattern:** 9 smurfs → 15 sub-threshold cash deposits → same-day transfer to one aggregator → one outbound transfer

**Planted:**
- `structured_deposit`: 15 cash deposits of 43.0–49.5M (threshold 50M) over 8 days
- `funnel_transfer`: each deposit forwarded the same day to the aggregator
- `consolidation`: aggregator sends ~96% of the total in one transfer (day 12)

**How it is hidden:**
- Amounts are not identical; legitimate salaries and cash deposits fall in the same 40–50M band
- Smurfs also have normal activity

**Indicators:** cash-in/transfer-out pairs on the same day; fan-in to one account; consolidation shortly after.
""",
    },
    "03": {
        "title": "Shell Company Network",
        "description": """
**Pattern:** Company A → B → C → A, 4 cycles over ~6 weeks

**Planted:**
- `round_trip`: 12 transfers between three corporate accounts (different customers),
  420–560M at the start of each cycle, ~3–7% retained at each hop,
  sequential invoice numbers with vague services (consulting / management / trading)

**How it is hidden:**
- Legitimate B2B invoices with the same description style, heavy-tailed amounts (median ~325M, some > 1B)
- Natural small cycles exist in the noise (false positives for naive cycle queries)

**Indicators:** repeated closed 3-cycle among the same companies; decreasing amounts; vague invoices.
""",
    },
    "04": {
        "title": "Terrorist Financing",
        "description": """
**Pattern:** many donors → charity → NGO → foreign-national account

**Planted:**
- `donation`: 50 non-corporate donors (incl. foreign nationals), 1–3 donations each of 1–5M over 60 days
- `aggregation`: charity forwards ~95% of each month's collection to the NGO (2 tranches)
- `foreign_transfer`: NGO forwards ~90% to a foreign national 2 days later

Charity/NGO are corporate accounts, preferring names starting with موسسه / سازمان.

**How it is hidden:**
- Legitimate merchants also receive many small payments (fan-in hubs)
- Donation descriptions are ordinary (کمک خیریه / نذر / empty)

**Indicators:** fan-in then rapid pass-through; charity does not hold funds; foreign end beneficiary.
""",
    },
    "05": {
        "title": "Account Takeover",
        "description": """
**Pattern:** stable retiree behaviour for 6 months, then a night-time drain

**Baseline (not labelled):** monthly 25M pension from a corporate pension payer (07:00–08:59),
2–3 small purchases and an ATM withdrawal per month. Victim account opened before 1395.

**Planted:**
- `takeover_transfer`: 500M to a recently opened account (00:00–04:59, mobile banking)
- `drain`: 200M, 180M, 150M to another beneficiary over the next 4 days, also at night

**How it is hidden:** the population contains legitimate 150–600M personal transfers (car, housing deposit).

**Indicators:** amount 20× the account's baseline; night hours; new beneficiaries.
""",
    },
    "06": {
        "title": "Trade-Based Money Laundering",
        "description": """
**Pattern:** importer → free-zone broker → foreign exporter, 5 cycles ~20 days apart

**Planted:**
- `inflated_invoice`: importer pays 0.9–1.2B per proforma
- `pass_through`: broker forwards ~85% to a foreign-national account 1–3 days later

Over-invoicing itself is not visible in payment data (would need customs declarations);
what is visible is the repeated pass-through with a fixed ~15% retention.

**How it is hidden:** legitimate B2B payments of similar size (some > 1B) and proforma-style descriptions.

**Indicators:** fixed retention ratio; same three parties; regular cadence; foreign end beneficiary.
""",
    },
    "07": {
        "title": "Insider Fraud (Bank Employee)",
        "description": """
**Pattern:** dormant accounts of one branch drained at the counter to a few mules

**Planted:**
- `unauthorized_transfer`: each victim (individual, opened before 1398, same bank and branch)
  sends 50–200M at the branch counter, roughly every 3 days
- `cash_out`: the receiving mule withdraws 85–95% in cash within 1–2 days

Victim count depends on how many eligible accounts the branch has (currently 6).

**How it is hidden:** victims are otherwise silent, so they never appear in noise; mules have normal activity.

**Indicators:** dormant accounts suddenly active; all victims share a branch; shared beneficiaries; quick cash-out.
""",
    },
    "08": {
        "title": "Circular Payments (Complex Network)",
        "description": """
**Pattern:** 18-account ring returning to the originator, plus 3 side paths

**Planted:**
- `ring_hop`: 18 hops, 1–4 business days apart (~7 weeks), 4–6% retained per hop
  (1B → ~400M back at the originator)
- `side_path`: originator → ring member → a member further along the ring (200M each)

**How it is hidden:** neutral descriptions; every ring account also does normal business.

**Indicators:** long cycle back to origin; monotonic amount decay; side paths that reconverge.
""",
    },
}

def generate_readme(scenario_num: str, transactions_file: str) -> str:
    """Generate README content for a scenario"""
    info = SCENARIO_INFO.get(scenario_num, {})

    if not info:
        return f"# Scenario {scenario_num}\n\nNo information available."

    readme_content = f"""# Scenario {scenario_num}: {info.get('title', 'Unknown')}

## Overview
{info['description']}

## Transaction Statistics
{stats(transactions_file)}

## File Structure
```
scenario_""" + scenario_num + """/
├── transactions.csv    # Bank-side view, no labels
├── ground_truth.csv    # transaction_id, role of every planted fraud transaction
└── README.md           # This file
```

## Data Fields

### transactions.csv Columns
| Column | Description |
|--------|-------------|
| transaction_id | Unique transaction reference |
| date | Transaction date (Solar Hijri YYYYMMDD) |
| time | Transaction time (HHMMSS) |
| sender_sheba | Originating account Sheba (empty for cash deposits) |
| receiver_sheba | Receiving account Sheba (empty for cash withdrawals) |
| amount | Amount in IRR (Iranian Rial) |
| currency | Currency code (IRR) |
| type | واریز نقدی (cash in), برداشت نقدی (cash out), انتقال داخلی (same bank), پایا (interbank < 150M), ساتنا (interbank ≥ 150M) |
| description | Transaction description/narrative |
| reference | Bank reference number |
| channel | اینترنت‌بانک (internet), موبایل‌بانک (mobile), شعبه (branch), ATM |
| status | Transaction status (completed) |

## Usage Examples

### Load Transactions in Python
```python
import pandas as pd

# Load transactions
df = pd.read_csv('transactions.csv', encoding='utf-8-sig')

# Convert amount to millions
df['amount_millions'] = df['amount'] / 1_000_000

# Score a detector against the planted labels
truth = pd.read_csv('ground_truth.csv', encoding='utf-8-sig')
df['is_planted'] = df['transaction_id'].isin(truth['transaction_id'])
```

### Analyze Account Relationships
```python
# Find accounts with unusual activity
account_activity = df.groupby('sender_sheba').agg({
    'amount': ['sum', 'count', 'mean'],
    'date': ['min', 'max']
})

# Identify circular flows
circular_pairs = df[df.apply(
    lambda x: x['receiver_sheba'] in df['sender_sheba'].values,
    axis=1
)]
```

## Detection Strategies

### Key Risk Indicators to Look For:
1. **Velocity Checks:** Unusual transaction frequency or speed
2. **Amount Patterns:** Round numbers, threshold avoidance
3. **Relationship Anomalies:** New beneficiaries, unusual connections
4. **Temporal Patterns:** Unusual timing, rapid sequences
5. **Cross-Account Analysis:** Shared branch, shared beneficiaries, account age

### Red Flags Specific to This Scenario:
- Review the fraud indicators listed in the overview section
- Cross-reference with accounts_master.csv for customer details
- Look for deviations from established baseline behavior
- Identify clustering patterns in time, amount, or geography

## References

### FATF Standards
- [FATF 40 Recommendations](https://www.fatf-gafi.org/publications/fatf-standards/)
- [FATF Typologies Reports](https://www.fatf-gafi.org/publications/typologies/)

### Iranian Regulations
- [Central Bank of Iran AML/CTF Regulations](https://www.cbi.ir/)
- [Iranian Banking Anti-Money Laundering Law](https://www.icana.ir/)

---
Generated for Iranian Banking Fraud Detection Analysis
"""

    return readme_content

def create_readme(scenario_dir: str, scenario_num: str):
    """Create README.md file for a scenario directory"""
    transactions_file = os.path.join(scenario_dir, "transactions.csv")

    if not os.path.exists(transactions_file):
        print(f"Warning: {transactions_file} not found, creating README anyway")

    readme_content = generate_readme(scenario_num, transactions_file)
    readme_file = os.path.join(scenario_dir, "README.md")

    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"Created {readme_file}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate README files for fraud detection scenarios')
    parser.add_argument('--scenarios', type=str, nargs='+', help='Scenario directories (e.g., scenario_01)')
    parser.add_argument('--scenario-numbers', type=str, nargs='+', help='Scenario numbers (e.g., 01 02 03)')
    parser.add_argument('--all', action='store_true', help='Generate READMEs for all scenarios 01-08')

    args = parser.parse_args()

    scenario_dirs = []

    if args.all:
        # Generate for all scenarios 01-08
        for i in range(1, 9):
            num_str = str(i).zfill(2)
            scenario_dirs.append((f"scenario_{num_str}", num_str))

    elif args.scenario_numbers:
        # Use provided scenario numbers
        for num in args.scenario_numbers:
            scenario_dirs.append((f"scenario_{num}", num))

    elif args.scenarios:
        # Use provided scenario directories
        for scenario_dir in args.scenarios:
            # Extract scenario number from directory name
            scenario_num = scenario_dir.replace('scenario_', '').replace('/', '')
            scenario_dirs.append((scenario_dir, scenario_num))

    else:
        print("Error: Must specify --all, --scenario-numbers, or --scenarios")
        return

    for scenario_dir, scenario_num in scenario_dirs:
        try:
            create_readme(scenario_dir, scenario_num)
        except Exception as e:
            print(f"Error creating README for {scenario_dir}: {e}")

if __name__ == '__main__':
    main()
