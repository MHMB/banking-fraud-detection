# Scenario 08: Circular Payments (Complex Network)

## Overview

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


## Transaction Statistics
- **Total Transactions:** ~150
- **Fraudulent Transactions:** ~70
- **Legitimate Transactions:** ~80

## File Structure
```
scenario_08/
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
