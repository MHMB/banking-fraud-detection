# Scenario 04: Terrorist Financing

## Overview

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


## Transaction Statistics
- **Total Transactions:** ~150
- **Fraudulent Transactions:** ~80
- **Legitimate Transactions:** ~70

## File Structure
```
scenario_04/
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
