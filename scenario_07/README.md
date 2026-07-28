# Scenario 07: Insider Fraud (Bank Employee)

## Overview

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


## Transaction Statistics
- **Total Transactions:** ~50
- **Fraudulent Transactions:** ~15
- **Legitimate Transactions:** ~35

## File Structure
```
scenario_07/
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
