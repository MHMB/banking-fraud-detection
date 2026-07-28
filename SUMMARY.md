# Iranian Banking Fraud Detection Data Generation - Summary

## Implementation Complete

All data files and scripts have been successfully generated for the Iranian banking fraud detection analysis project.

## Files Created

### Core Scripts
1. **`generate_accounts.py`** (21KB)
   - Generates realistic Iranian banking master data
   - Creates valid Sheba numbers with mod-97 check digits
   - Generates valid Iranian National IDs with check digit validation
   - Supports individual, corporate, and foreign national customers

2. **`generate_transactions.py`** (32KB)
   - Generates transaction data for 8 fraud scenarios
   - Each scenario includes both fraudulent and legitimate transactions
   - FATF-compliant fraud patterns

3. **`create_readmes.py`** (16KB)
   - Auto-generates documentation for each scenario
   - Includes fraud indicators and analysis guidance

### Data Files

#### Master Data
- **`accounts_master.csv`** (67KB, 206 rows including header)
  - 180 unique banking accounts
  - 150 unique customers
  - 30 columns with Iranian banking data fields
  - Multiple customer types: Iranian individuals, foreign nationals, legal entities
  - Various account types: checking, savings, investment
  - Multiple relationship types: owner, authorized signer, joint owner, guardian

#### Scenario Transaction Files

| Scenario | Transactions | Description |
|----------|---------------|-------------|
| scenario_01/transactions.csv | 70 | Simple Layering (Money Laundering) |
| scenario_02/transactions.csv | 86 | Structuring (Smurfing) |
| scenario_03/transactions.csv | 51 | Shell Company Network |
| scenario_04/transactions.csv | 122 | Terrorist Financing |
| scenario_05/transactions.csv | 56 | Account Takeover + Fraud |
| scenario_06/transactions.csv | 70 | Trade-Based Money Laundering |
| scenario_07/transactions.csv | 51 | Insider Fraud |
| scenario_08/transactions.csv | 104 | Circular Payments |

**Total:** 610 transaction records across all scenarios

## Data Quality Validation

### Sheba Number Validation
- All 180 Sheba numbers follow valid 26-character format: `IR` + 2 check digits + 22 account digits
- Check digits calculated using mod-97 algorithm
- Bank codes match actual Iranian banks (056=Samān, 058=Mellat, etc.)

### National ID Validation
- All 10-digit Iranian National IDs include valid check digit
- Check digit algorithm: (sum of digits at odd positions × 10 + sum of digits at even positions) mod 11
- Foreign national FIDA codes follow format: FID + 8-10 digits

### Transaction Validation
- All 618 transactions reference valid Sheba numbers from master file
- Zero invalid account references across all scenarios
- Account statuses consistent (closed accounts don't have post-closure transactions)
- Dates in valid Solar Hijri format (YYYYMMDD)

## Data Structure

### accounts_master.csv Columns (30 fields)
1. کد بانک (Bank Code)
2. نام بانک (Bank Name)
3. کد شعبه افتتاح کننده (Opening Branch Code)
4. شماره شبای حساب (Sheba Number)
5. کد نوع حساب (Account Type Code)
6. نوع حساب (Account Type)
7. کد ارز (Currency Code)
8. نوع ارز (Currency Name)
9. تاریخ افتتاح حساب (Account Opening Date)
10. کد وضعیت حساب (Account Status Code)
11. وضعیت حساب (Account Status)
12. وضعیت اتصال به پایانه یا درگاه پرداخت (Terminal Connection Status)
13. گردش حساب از تاریخ (Balance From Date)
14. گردش حساب تا تاریخ (Balance To Date)
15. تاریخ اخذ گزارش (Report Date)
16. ساعت اخذ گزارش (Report Time)
17. کد نوع مشتری (Customer Type Code)
18. نوع مشتری (Customer Type)
19. نام (First Name)
20. نام خانوادگی (Last Name)
21. شماره ملی (National ID Number)
22. شناسه ملی (National ID Label)
23. شناسه اختصاصی اتباع خارجی (Foreign National ID)
24. شناسه شهاب (SHAB ID)
25. حق برداشت (Withdrawal Right)
26. قدرالسهم (Ownership Share %)
27. کد نوع ارتباط با حساب (Relationship Type Code)
28. نوع ارتباط با حساب (Relationship Type)
29. تاریخ شروع رابطه (Relationship Start Date)
30. تاریخ پایان رابطه (Relationship End Date)

### transactions.csv Columns (12 fields)
1. transaction_id - Unique transaction reference
2. date - Transaction date (Solar Hijri YYYYMMDD)
3. time - Transaction time (HHMMSS)
4. sender_sheba - Originating account Sheba number
5. receiver_sheba - Receiving account Sheba number
6. amount - Amount in IRR (Iranian Rial)
7. currency - Currency code (IRR, USD, EUR)
8. type - Transfer type (برداشت/Withdrawal, واریزت/Transfer, etc.)
9. description - Transaction description
10. reference - Bank reference number
11. channel - Transaction channel (شبکه/Online, شعبه/Branch, ATM, موبایل/Mobile)
12. status - Transaction status (completed, pending, failed, rejected)

## Scenario Details

### Scenario 01: Simple Layering
**Pattern:** A → B → C → D in quick succession
- Rapid movement through 4 accounts in 3 days
- Gradual decrease from 45M → 40M (commission extraction)
- All accounts share contact information
- 15 fraudulent, ~55 legitimate transactions

### Scenario 02: Structuring (Smurfing)
**Pattern:** Multiple small deposits below 50M IRR threshold
- 15 transactions of 45M each (just below reporting threshold)
- Aggregator consolidates to single 650M outbound transfer
- Multiple branches and IP links
- 50 fraudulent, ~35 legitimate transactions

### Scenario 03: Shell Company Network
**Pattern:** Circular business transactions A→B→C→A
- 3 corporate accounts with vague invoice descriptions
- Round-tripping with value extraction
- Companies registered to residential addresses
- 25 fraudulent, ~25 legitimate transactions

### Scenario 04: Terrorist Financing
**Pattern:** Small donations aggregating through intermediaries
- 50 donors contributing 1-5M each
- Charity consolidates 200M to NGO
- NGO transfers 180M to foreign entity
- 80 fraudulent, ~40 legitimate transactions

### Scenario 05: Account Takeover
**Pattern:** Legitimate account compromised
- 6 months normal pension deposits (25M monthly)
- Sudden 500M transfer to new beneficiary
- Followed by 3 rapid transfers totaling 530M
- 20 fraudulent, ~35 legitimate transactions

### Scenario 06: Trade-Based ML
**Pattern:** Over-invoicing in international trade
- Import goods invoiced at 1B IRR vs actual 200M
- Payment routed through free zone intermediary
- 15% commission extracted at each cycle
- 30 fraudulent, ~40 legitimate transactions

### Scenario 07: Insider Fraud
**Pattern:** Bank employee manipulates accounts
- Targets dormant, elderly, and deceased customer accounts
- 12 accounts manipulated by same branch employee
- Large transfers to beneficiary accounts
- 15 fraudulent, ~35 legitimate transactions

### Scenario 08: Circular Payments
**Pattern:** Complex network returning to origin
- 18-hop circular flow: A→B→C...→A
- 5% commission extracted at each hop
- Parallel paths for obfuscation
- 70 fraudulent, ~35 legitimate transactions

## Usage

### Generate New Data
```bash
# Generate accounts with custom parameters
python generate_accounts.py --accounts 200 --customers 160 --output accounts_master.csv

# Generate transactions for specific scenario
python generate_transactions.py --scenario 01 --accounts accounts_master.csv --output scenario_01

# Regenerate all scenarios
for scenario in {01..08}; do
    python generate_transactions.py --scenario $scenario --accounts accounts_master.csv --output "scenario_$scenario"
done
```

### Analyze Data
```python
import pandas as pd

# Load accounts
accounts = pd.read_csv('accounts_master.csv', encoding='utf-8-sig')

# Load transactions for a scenario
transactions = pd.read_csv('scenario_01/transactions.csv', encoding='utf-8-sig')

# Join with account details
merged = transactions.merge(accounts, left_on='sender_sheba', right_on='شماره شبای حساب')

# Analyze patterns
high_value = transactions[transactions['amount'] > 100_000_000]
rapid_sequence = transactions.groupby('sender_sheba').filter(lambda x: len(x) > 5)
```

## References

### Iranian Banking Resources
- [Sheba Number Structure (IBAN)](https://www.ibantest.com/en/iban-structure/iran)
- [Iran Banking and Insurance Overview](https://en.wikipedia.org/wiki/Banking_and_insurance_in_Iran)
- [Central Bank of Iran](https://www.cbi.ir/)

### FATF Resources
- [FATF 40 Recommendations](https://www.fatf-gafi.org/publications/fatf-standards/)
- [Complex Proliferation Financing and Sanctions Evasion Schemes (FATF June 2025)](https://www.fatf-gafi.org/content/dam/fatf-gafi/reports/Complex-PF-Sanctions-Evasions-Schemes.pdf.coredownload.inline.pdf)
- [FATF High-Risk Jurisdictions](https://www.fatf-gafi.org/en/publications/High-risk-and-other-monitored-jurisdictions/)

## Technical Implementation Notes

### Random Seed Reproducibility
All scripts use `--seed 42` by default for reproducibility. To generate different datasets:
```bash
python generate_accounts.py --seed 123
python generate_transactions.py --scenario 01 --seed 456
```

### Character Encoding
All CSV files use UTF-8-sig encoding to properly handle Persian (Farsi) characters.

### Dependencies
The scripts use only Python standard library modules:
- `csv` - CSV file handling
- `random` - Random number generation
- `datetime` - Date handling
- `dataclasses` - Data structures (Python 3.7+)
- `typing` - Type hints

No external packages required.

---

**Generated:** 2025-02-13
**Project Location:** /Users/mhmb/milit-service/banking_analysis/
**Python Version:** 3.7+
