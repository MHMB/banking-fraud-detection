#!/usr/bin/env python3
"""
Generate README.md files for each fraud detection scenario
Creates scenario documentation with fraud indicators and statistics
"""

import os
from typing import Dict, List

SCENARIO_INFO = {
    "01": {
        "title": "Simple Layering (Money Laundering)",
        "description": """
**Pattern:** Customer A → B → C → D in quick succession

This scenario demonstrates a classic layering technique where illicit funds are moved through multiple accounts in rapid succession to obscure their origin. Each layer extracts a commission, gradually reducing the amount.

**Account Characteristics:**
- 4 individual accounts (all active)
- Shared attributes: same phone number or IP address
- Customer A: New account (opened recently)
- Customers B, C, D: Established accounts

**Fraudulent Transaction Flow:**
- Day 1: A deposits 45M IRR (cash at branch)
- Day 1: A → B transfer 44.5M (online banking)
- Day 2: B → C transfer 44M (mobile)
- Day 3: C → D transfer 43.5M (online)
- Day 4: D withdraws 40M (cash at branch)

**Fraud Indicators:**
- Rapid movement through multiple accounts (3 days)
- Gradual decrease (commission extraction at each layer)
- All accounts share contact information
- Unusual pattern for customer D (normally low activity)
""",
        "total_transactions": "~80",
        "fraudulent_transactions": "~15",
        "legitimate_transactions": "~65",
    },

    "02": {
        "title": "Structuring (Smurfing)",
        "description": """
**Pattern:** Multiple small deposits below reporting threshold

This scenario demonstrates structuring (also known as smurfing), where large amounts are broken into multiple smaller transactions to avoid currency transaction reporting (CTR) requirements. In Iran, transactions above 50M IRR trigger reporting requirements.

**Account Characteristics:**
- 1 primary aggregator account
- 8-10 source accounts (some legitimate customers, some money mules)
- Mix of individual and joint accounts

**Fraudulent Transaction Flow:**
- 15 transactions of 45M IRR each (threshold: 50M)
- Spread across 10 days
- Multiple branches (3-4 different branch codes)
- Some from same IP address (different accounts)
- Final: aggregator account consolidates to single outbound transfer of 650M

**Fraud Indicators:**
- Repeated amounts just below threshold
- Multiple accounts linked by IP/device
- Temporal clustering (same time window daily)
- Final consolidation indicates structuring purpose
""",
        "total_transactions": "~120",
        "fraudulent_transactions": "~50",
        "legitimate_transactions": "~70",
    },

    "03": {
        "title": "Shell Company Network",
        "description": """
**Pattern:** Circular business transactions with no legitimate purpose

This scenario demonstrates the use of shell companies to create circular transactions that appear legitimate but serve no business purpose other than to move funds and extract value.

**Account Characteristics:**
- 3 corporate accounts (registered companies)
- 2 individual accounts (company directors)
- All companies registered to same residential address
- Company types: "consulting services", "trading company", "investment LLC"

**Fraudulent Transaction Flow:**
- Day 1: Company A → Company B: 500M IRR (invoice #INV-001)
- Day 3: Company B → Company C: 450M IRR (invoice #INV-002)
- Day 5: Company C → Company A: 480M IRR (invoice #INV-003)
- Repeat cycle 2-3 times with slight variations
- All invoices for vague services ("consulting", "management fees")

**Fraud Indicators:**
- Circular flow of funds (A→B→C→A)
- No legitimate business purpose (vague invoices)
- Companies at residential addresses
- No real business operations (no employees, no actual trade)
- Round-tripping with value extraction
""",
        "total_transactions": "~70",
        "fraudulent_transactions": "~25",
        "legitimate_transactions": "~45",
    },

    "04": {
        "title": "Terrorist Financing",
        "description": """
**Pattern:** Small donations aggregating through intermediaries

This scenario demonstrates terrorist financing where small donations from many individuals are aggregated through charitable organizations and then transferred to high-risk jurisdictions.

**Account Characteristics:**
- 40-50 individual donor accounts (small amounts)
- 1 charity organization account
- 1 NGO account
- 1 foreign entity account (high-risk jurisdiction)
- 5-10 accounts with foreign national IDs

**Fraudulent Transaction Flow:**
- 50 donors: 1-5M IRR each to charity (mixed dates over 2 months)
- Charity consolidates and transfers 200M to NGO (single transaction)
- NGO → Foreign entity: 180M IRR (converted to foreign currency equivalent)
- Some donors use crypto exchanges (if modeled)
- Cash deposits at multiple branches

**Fraud Indicators:**
- Aggregation pattern (many small → one large)
- Rapid pass-through (charity doesn't hold funds, transfers immediately)
- Ultimate beneficiary in high-risk jurisdiction
- Charity with no transparent operations
- Some donors are foreign nationals
""",
        "total_transactions": "~150",
        "fraudulent_transactions": "~80",
        "legitimate_transactions": "~70",
    },

    "05": {
        "title": "Account Takeover + Fraud",
        "description": """
**Pattern:** Legitimate account compromised, behavior changes

This scenario demonstrates account takeover where a legitimate customer's account is compromised, leading to unauthorized access and fraudulent transactions that deviate from the established behavior pattern.

**Account Characteristics:**
- Customer X (long-standing account, opened 1390, regular pension deposits)
- Customer Y (new account, suspicious)
- Customer Z (offshore connection)

**Fraudulent Transaction Flow:**

*Before takeover (months 1-6):*
- Regular pension deposits: 25M IRR monthly
- Small withdrawals: 2-5M for living expenses
- Normal activity pattern

*Takeover event:*
- Change of contact info (email, phone added to account)
- New authorized signer added (Customer Y)
- Large transfer to new beneficiary: 500M IRR

*After takeover (months 7-9):*
- 3 rapid transfers: 200M, 180M, 150M to Customer Z
- Account status changed to closed after final transfer
- Customer complaint filed (after account emptied)

**Fraud Indicators:**
- Sudden change in transaction behavior
- New relationship (authorized signer) added unexpectedly
- Large transfers to new beneficiaries (not historical pattern)
- Account closed immediately after funds transferred
- Deviation from established baseline
""",
        "total_transactions": "~60",
        "fraudulent_transactions": "~20",
        "legitimate_transactions": "~40",
    },

    "06": {
        "title": "Trade-Based Money Laundering",
        "description": """
**Pattern:** Over/under-invoicing in international trade

This scenario demonstrates trade-based money laundering where the value transferred between parties is misrepresented through false invoicing, allowing funds to move across borders under the guise of legitimate trade.

**Account Characteristics:**
- Company A (Iran importer - "Tehran Trading Co")
- Company B (UAE exporter - "Gulf Trading LLC")
- Company C (intermediary in free zone)
- Company D (another shell company)

**Fraudulent Transaction Flow:**
- Trade transaction: Import goods from B
- Invoice shows: 1M USD equivalent
- Actual value: 200K USD (80% over-invoicing)
- Payment route: A → C → B (through free zone)
- C charges 15% commission (150K USD)
- Multiple similar transactions over 3 months
- Documents show electronics imports (inflated values)

**Fraud Indicators:**
- Trade invoices significantly inflated
- Routing through free zone/intermediaries
- Value transfer through trade misrepresentation
- Shell companies in free trade zones involved
- Multiple high-value similar transactions
""",
        "total_transactions": "~90",
        "fraudulent_transactions": "~30",
        "legitimate_transactions": "~60",
    },

    "07": {
        "title": "Insider Fraud (Bank Employee)",
        "description": """
**Pattern:** Bank employee manipulates accounts

This scenario demonstrates insider fraud where a bank employee abuses their access to customer accounts to initiate unauthorized transactions, targeting vulnerable customers.

**Account Characteristics:**
- 5 dormant accounts (not used in 2+ years)
- 3 accounts of elderly customers (limited activity)
- 2 accounts of deceased customers (status not yet updated)
- 2 accounts with minimal KYC data
- All manipulated by same bank employee (branch: 5692412)

**Fraudulent Transaction Flow:**
- Dormant accounts suddenly receive deposits
- New "customer" accounts opened with minimal KYC
- Elderly customer accounts: unusual large transfers out
- Deceased customer accounts: transfers initiated before death recorded
- All transfers go to accounts controlled by employee or associates
- 2 accounts: email/phone changed before large transfers

**Fraud Indicators:**
- Dormant accounts reactivated without customer initiation
- Accounts of vulnerable customers (elderly, deceased) targeted
- All manipulated accounts handled by same branch/employee
- KYC incomplete on newly opened accounts
- Pattern of transfers to same ultimate beneficiaries
""",
        "total_transactions": "~50",
        "fraudulent_transactions": "~15",
        "legitimate_transactions": "~35",
    },

    "08": {
        "title": "Circular Payments (Complex Network)",
        "description": """
**Pattern:** Money flows through complex network returning to origin

This scenario demonstrates a complex circular payment network designed to obscure the audit trail through multiple hops, delays, and parallel paths.

**Account Characteristics:**
- 20 accounts forming circular network
- 1 originator account (beneficiary of final flow)
- Mix of individual and corporate accounts
- Multiple banks involved (5-6 different bank codes)

**Fraudulent Transaction Flow:**
- Account A → Account B → Account C ... → Account S → Account T → Account A
- Path length: 15-18 hops
- Delays vary: immediate, 1 day, 3 days, 5 days (randomized)
- Amount decreases gradually (commissions extracted at each hop): 1B → 950M → 910M ...
- Some branches split and reconverge (parallel paths)
- Total duration: 45 days from start to return

**Fraud Indicators:**
- Circular flow where originator is ultimate beneficiary
- Complex network to obscure audit trail
- Commissions extracted at each layer
- Temporal delays to avoid real-time detection
- Multiple parallel paths for additional obfuscation
""",
        "total_transactions": "~150",
        "fraudulent_transactions": "~70",
        "legitimate_transactions": "~80",
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
- **Total Transactions:** {info['total_transactions']}
- **Fraudulent Transactions:** {info['fraudulent_transactions']}
- **Legitimate Transactions:** {info['legitimate_transactions']}

## File Structure
```
scenario_""" + scenario_num + """/
├── transactions.csv    # Transaction data for this scenario
└── README.md          # This file
```

## Data Fields

### transactions.csv Columns
| Column | Description |
|--------|-------------|
| transaction_id | Unique transaction reference |
| date | Transaction date (Solar Hijri YYYYMMDD) |
| time | Transaction time (HHMMSS) |
| sender_sheba | Originating account Sheba number |
| receiver_sheba | Receiving account Sheba number |
| amount | Amount in IRR (Iranian Rial) |
| currency | Currency code (IRR, USD, EUR) |
| type | Transfer type (برداشت/Withdrawal, واریزت/Transfer, واریت واریزت/Wire) |
| description | Transaction description/narrative |
| reference | Bank reference number |
| channel | Transaction channel (شبکه/Online, شعبه/Branch, ATM, موبایل/Mobile) |
| status | Transaction status (completed, pending, failed, rejected) |

## Usage Examples

### Load Transactions in Python
```python
import pandas as pd

# Load transactions
df = pd.read_csv('transactions.csv', encoding='utf-8-sig')

# Convert amount to millions
df['amount_millions'] = df['amount'] / 1_000_000

# Filter fraudulent patterns
high_value = df[df['amount'] > 100_000_000]
rapid_transfers = df[df.duplicated(subset=['sender_sheba'], keep=False)]
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
5. **Cross-Account Analysis:** Shared identifiers (IP, device, phone)

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
