# Scenario 05: Account Takeover + Fraud

## Overview

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


## Transaction Statistics
- **Total Transactions:** ~60
- **Fraudulent Transactions:** ~20
- **Legitimate Transactions:** ~40

## File Structure
```
scenario_05/
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
