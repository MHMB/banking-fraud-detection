# Scenario 03: Shell Company Network

## Overview

**Pattern:** Company A → B → C → A, 4 cycles over ~6 weeks

**Planted:**
- `round_trip`: 12 transfers between three corporate accounts (different customers),
  420–560M at the start of each cycle, ~3–7% retained at each hop,
  sequential invoice numbers with vague services (consulting / management / trading)

**How it is hidden:**
- Legitimate B2B invoices with the same description style, heavy-tailed amounts (median ~325M, some > 1B)
- Natural small cycles exist in the noise (false positives for naive cycle queries)

**Indicators:** repeated closed 3-cycle among the same companies; decreasing amounts; vague invoices.


## Transaction Statistics
- **Total Transactions:** 132
- **Planted Fraud Transactions:** 12
- **Background (legitimate) Transactions:** 120
- **Period:** 14030101 – 14030215

## File Structure
```
scenario_03/
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
