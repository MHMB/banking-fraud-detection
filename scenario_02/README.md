# Scenario 02: Structuring (Smurfing)

## Overview

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


## Transaction Statistics
- **Total Transactions:** ~120
- **Fraudulent Transactions:** ~50
- **Legitimate Transactions:** ~70

## File Structure
```
scenario_02/
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
