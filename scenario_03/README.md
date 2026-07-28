# Scenario 03: Shell Company Network

## Overview

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


## Transaction Statistics
- **Total Transactions:** ~70
- **Fraudulent Transactions:** ~25
- **Legitimate Transactions:** ~45

## File Structure
```
scenario_03/
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
