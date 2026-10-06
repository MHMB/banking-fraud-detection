#!/usr/bin/env python3
"""
Generate Iranian Banking Master Data for Fraud Detection Scenarios
Creates realistic accounts_master.csv with valid Iranian banking data
"""

import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Iranian Bank Codes
# Iranian bank identifiers as they appear in Sheba digits 5-7
IRANIAN_BANKS = {
    "056": "بانک سامان",
    "012": "بانک ملت",
    "057": "بانک پاسارگاد",
    "017": "بانک ملی",
    "018": "بانک تجارت",
    "015": "بانک سپه",
    "019": "بانک صادرات",
    "016": "بانک کشاورزی",
    "059": "بانک سینا",
    "061": "بانک شهر",
}

# Account Types
ACCOUNT_TYPES = [
    (4, "حساب هاي جاري با دسته چک"),
    (1, "حساب هاي جاري بدون دسته چک"),
    (2, "حساب پس انداز"),
    (3, "حساب سرمایه گذاري كوتاه مدت"),
    (5, "حساب سرمایه گذاري بلند مدت"),
]

# Customer Types
CUSTOMER_TYPES = [
    (1, "حقيقي ايراني"),
    (2, "حقيقي اتباع خارجي"),
    (3, "حقوقي"),
]

# Relationship Types
RELATIONSHIP_TYPES = [
    (1, "صاحب حساب", 100),      # Account Owner - 100% share
    (2, "صاحب امضا", 50),        # Authorized Signer - limited withdrawal
    (3, "شریک", 50),             # Joint Owner - partial ownership
    (4, "قیم", 100),             # Legal Guardian - for minors
    (5, "وکیل قانونی", 100),     # Legal Representative
]

# Account Statuses
ACCOUNT_STATUSES = [
    (1, "باز"),           # Active
    (2, "بسته"),          # Closed
    (3, "مسدود"),         # Frozen
]

# Persian Names for Individuals
FIRST_NAMES_MALE = [
    "علی", "محمد", "رضا", "حسین", "مهدی", "امیر", "آرش", "کاوهان",
    "سهیل", "پویا", "سینا", "محمد‌رضا", "احسان", "فرهاد", "بهنام",
    "آرین", "نیما", "شاهد", "عرفان", "یاسر", "کامران", "بیژن",
]

FIRST_NAMES_FEMALE = [
    "مریم", "فاطمه", "زهرا", "سارا", "نگین", "مهرانه", "هستی", "لیلا",
    "رقیه", "سمیرا", "نیلوفر", "شقایق", "زینب", "ناژین", "پریسا",
    "سپیده", "مینا", "رویا", "الهام", "نسیم", "سپهر",
]

LAST_NAMES = [
    "محمدی", "رضایی", "کریمی", "حسینی", "احمدی", "موسوی", "حسین‌پور",
    "کریمی‌پور", "محمدی‌نژاد", "جعفری", "نوری", "قاسمی", "رحمتی",
    "صادقی", "باقری", "شمس", "زارعی", "کاظمی", "فراهانی", "بهرامی",
    "هدایت", "امانی", "جلالی", "یزدی", "یزدی‌پور", "نوری‌پور",
]

# Company Names
COMPANY_PREFIXES = [
    "شرکت", "گروه", "هلدینگ", "موسسه", "سازمان",
]

COMPANY_SUFFIXES = [
    "تجاری", "بازرگانی", "سرمایه‌گذاری", "توسعه", "مشاوره", "فنی",
    "صنعتی", "تولیدی", "خدماتی", "علمی", "تحقیقاتی",
]

# Persian Cities
CITIES = [
    "تهران", "مشهد", "اصفهان", "شیراز", "تبریز", "کرج", "قم", "اهواز",
    "کرمانشاه", "رشت", "اوزمیه", "زنجان", "ساری", "همدان", "یاسوج",
    "سنندج", "ایلام", "خرم‌آباد", "زاهدان", "اردبیل",
]

# Street Types
STREET_TYPES = [
    "خیابان", "خیابان", "بلوار", "کوچه", "خیابان",
]


class SolarHijriDate:
    """Convert and generate Solar Hijri dates"""

    @staticmethod
    def random_date(start_year: int = 1390, end_year: int = 1402) -> str:
        """Generate random Solar Hijri date in YYYYMMDD format"""
        year = random.randint(start_year, end_year)
        month = random.randint(1, 12)
        day = random.randint(1, 29)  # Simplified (not month-specific)
        return f"{year}{month:02d}{day:02d}"

    @staticmethod
    def random_time() -> str:
        """Generate random time in HHMMSS format"""
        hour = random.randint(8, 20)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        return f"{hour:02d}{minute:02d}{second:02d}"

    @staticmethod
    def today() -> str:
        """Return today's date in Solar Hijri format (approximate)"""
        # 2025-02-13 ≈ 1403-11-24 (approximate conversion)
        return "14031124"

class IranianIDGenerator:
    """Generate valid Iranian identification numbers"""

    @staticmethod
    def national_id() -> str:
        """Generate valid 10-digit Iranian National ID with check digit"""
        # Generate first 9 digits
        base = str(random.randint(1000000, 999999999)).zfill(9)

        # Calculate check digit
        check = IranianIDGenerator._calculate_national_id_check(base)

        return base + str(check)

    @staticmethod
    def _calculate_national_id_check(base: str) -> int:
        """Calculate Iranian National ID check digit"""
        check = 0
        for i in range(9):
            check += int(base[i]) * (10 - i)

        remainder = check % 11

        if remainder < 2:
            return remainder
        else:
            return 11 - remainder

    @staticmethod
    def shab_id() -> str:
        """Generate 16-digit SHAHAB identifier"""
        return str(random.randint(10**15, 10**16 - 1))

    @staticmethod
    def legal_entity_id() -> str:
        """Generate valid 11-digit legal-entity national ID (شناسه ملی)"""
        base = str(random.randint(10**9, 10**10 - 1))
        d = int(base[9]) + 2
        coef = [29, 27, 23, 19, 17] * 2
        check = sum((int(c) + d) * k for c, k in zip(base, coef)) % 11
        return base + str(0 if check == 10 else check)

    @staticmethod
    def fida_code() -> str:
        """Generate FIDA code for foreign nationals (FID + 8-10 digits)"""
        digits = random.randint(8, 10)
        return "FID" + ''.join(str(random.randint(0, 9)) for _ in range(digits))

class ShebaGenerator:
    """Generate valid Iranian Sheba numbers (IBAN format)"""

    @staticmethod
    def generate(bank_code: str) -> str:
        """Generate valid 26-character Sheba number for given bank"""
        # Account number: 22 digits
        account_number = ''.join(str(random.randint(0, 9)) for _ in range(22))

        # Insert bank code at start of account number
        account_with_bank = bank_code + account_number[len(bank_code):]

        # Calculate check digits using mod-97
        check_digits = ShebaGenerator._calculate_check_digits(account_with_bank)

        return "IR" + check_digits + account_with_bank

    @staticmethod
    def _calculate_check_digits(account: str) -> str:
        """Calculate 2-digit check digits for Sheba using mod-97"""
        # Convert to digits (I=19, R=28)
        digit_str = str(int(account)) + "182700"  # Move and add country code

        # Mod 97
        remainder = int(digit_str) % 97
        check = 98 - remainder

        return str(check).zfill(2)

class CustomerGenerator:
    """Generate customer data"""

    def __init__(self):
        self.used_national_ids = set()

    def generate_individual(self) -> Dict:
        """Generate individual customer data"""
        gender = random.choice(['male', 'female'])

        if gender == 'male':
            first_name = random.choice(FIRST_NAMES_MALE)
        else:
            first_name = random.choice(FIRST_NAMES_FEMALE)

        last_name = random.choice(LAST_NAMES)
        customer_type_code = 1  # Iranian individual

        # Generate unique national ID
        while True:
            national_id = IranianIDGenerator.national_id()
            if national_id not in self.used_national_ids:
                self.used_national_ids.add(national_id)
                break

        shab_id = IranianIDGenerator.shab_id()

        return {
            'customer_type_code': customer_type_code,
            'customer_type': "حقيقي ايراني",
            'first_name': first_name,
            'last_name': last_name,
            'national_id': national_id,
            'national_id_label': 'شماره ملی',
            'fida_code': '',
            'shab_id': shab_id,
            'gender': gender,
        }

    def generate_foreign_national(self) -> Dict:
        """Generate foreign national customer data"""
        first_name = random.choice(["عبدالله", "نورمحمد", "غلام‌سخی", "محمدنبی", "حیدر", "علی‌اکبر"])
        last_name = random.choice(["احمدزی", "نوری", "حیدری", "الموسوی", "رحیمی", "هزاره"])
        customer_type_code = 2  # Foreign national

        fida_code = IranianIDGenerator.fida_code()
        shab_id = IranianIDGenerator.shab_id()

        return {
            'customer_type_code': customer_type_code,
            'customer_type': "حقيقي اتباع خارجي",
            'first_name': first_name,
            'last_name': last_name,
            'national_id': '',
            'national_id_label': '',
            'fida_code': fida_code,
            'shab_id': shab_id,
            'gender': 'male',
        }

    def generate_company(self) -> Dict:
        """Generate corporate customer data"""
        prefix = random.choice(COMPANY_PREFIXES)
        suffix = random.choice(COMPANY_SUFFIXES)
        company_name = f"{prefix} {random.choice(LAST_NAMES)} {suffix}"

        customer_type_code = 3  # Legal entity
        national_id = IranianIDGenerator.legal_entity_id()
        shab_id = IranianIDGenerator.shab_id()

        return {
            'customer_type_code': customer_type_code,
            'customer_type': "حقوقي",
            'first_name': '',
            'last_name': company_name,
            'national_id': national_id,
            'national_id_label': 'شناسه ملی',
            'fida_code': '',
            'shab_id': shab_id,
            'gender': 'corporate',
        }

class AccountGenerator:
    """Generate bank account data"""

    def __init__(self, num_accounts: int = 180, num_customers: int = 150):
        self.num_accounts = num_accounts
        self.num_customers = num_customers
        self.customer_gen = CustomerGenerator()
        self.accounts = []

    def generate_address(self) -> str:
        """Generate Persian address"""
        city = random.choice(CITIES)
        street_type = random.choice(STREET_TYPES)
        street_name = random.choice([
            "انقلاب", "آزادی", "ولیعصر", "انصاری", "مطهری", "شریعتی",
            "قاضی", "فلسطین", "جمهوری", "ولیعصر", "تهران", "کشاورز",
        ])
        building_num = random.randint(1, 500)
        postal_code = ''.join(str(random.randint(0, 9)) for _ in range(10))

        return f"{street_type} {street_name}، پلاک {building_num}، {city} - کد پستی {postal_code}"

    def generate_phone(self) -> str:
        """Generate Iranian phone number"""
        return f"09{random.randint(10, 39)}{random.randint(1000000, 9999999)}"

    def generate_email(self, first_name: str, last_name: str) -> str:
        """Generate email address"""
        domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
        # Transliterate Persian to Latin
        first = first_name.replace("‌", "").replace("آ", "a").replace("ا", "a")
        last = last_name.replace("‌", "")
        domain = random.choice(domains)
        return f"{first}.{last}{random.randint(10, 99)}@{domain}".lower()

    def generate_accounts(self) -> List[Dict]:
        """Generate all accounts"""
        customers = []

        # Generate customers
        for _ in range(self.num_customers):
            customer_type = random.choices(
                ['individual', 'foreign', 'company'],
                weights=[0.70, 0.10, 0.20],
                k=1
            )[0]

            if customer_type == 'individual':
                customer = self.customer_gen.generate_individual()
            elif customer_type == 'foreign':
                customer = self.customer_gen.generate_foreign_national()
            else:
                customer = self.customer_gen.generate_company()

            customers.append(customer)

        # Each bank has a few branches; an account is opened at one of its bank's branches
        branches = {code: [str(random.randint(1000, 9999)) for _ in range(3)] for code in IRANIAN_BANKS}

        # Assign customers to accounts (some accounts have multiple customers)
        customer_index = 0
        for i in range(self.num_accounts):
            bank_code = random.choice(list(IRANIAN_BANKS.keys()))
            bank_name = IRANIAN_BANKS[bank_code]
            branch_code = random.choice(branches[bank_code])
            sheba = ShebaGenerator.generate(bank_code)

            account_type_code, account_type = random.choice(ACCOUNT_TYPES)
            account_status_code, account_status = random.choices(
                ACCOUNT_STATUSES,
                weights=[0.85, 0.10, 0.05],  # 85% active, 10% closed, 5% frozen
                k=1
            )[0]

            opening_date = SolarHijriDate.random_date(1389, 1402)
            current_date = SolarHijriDate.today()
            report_time = SolarHijriDate.random_time()

            # Primary owner plus 0-2 joint owners / authorized signers
            num_relationships = random.choices([1, 2, 3], weights=[0.85, 0.12, 0.03], k=1)[0]
            relationships = []
            for r in range(num_relationships):
                customer = customers[customer_index % len(customers)]
                customer_index += 1
                rel_code = 1 if r == 0 else random.choice([2, 3])  # owner, then signer or joint owner
                _, rel_name, _ = RELATIONSHIP_TYPES[rel_code - 1]
                relationships.append({
                    'customer': customer,
                    'relationship_code': rel_code,
                    'relationship_type': rel_name,
                    'share': 0,
                    'has_withdrawal': True,
                    'start_date': opening_date,
                    'end_date': '',
                })
            # Owners split the account equally; signers hold no share
            owners = [rel for rel in relationships if rel['relationship_code'] in (1, 3)]
            for rel in owners:
                rel['share'] = 100 // len(owners)
            owners[0]['share'] += 100 - sum(rel['share'] for rel in owners)

            account = {
                'bank_code': bank_code,
                'bank_name': bank_name,
                'branch_code': branch_code,
                'sheba': sheba,
                'account_type_code': account_type_code,
                'account_type': account_type,
                'currency_code': 'IRR',
                'currency_name': 'Iranian Rial',
                'opening_date': opening_date,
                'status_code': account_status_code,
                'status': account_status,
                'terminal_connection': 'ندارد',
                'balance_from_date': opening_date,
                'balance_to_date': current_date,
                'report_date': current_date,
                'report_time': report_time,
                'relationships': relationships,
            }

            self.accounts.append(account)

        return self.accounts

def write_accounts_csv(accounts: List[Dict], output_file: str):
    """Write accounts to CSV file in specified format"""

    fieldnames = [
        'کد بانک', 'نام بانک', 'کد شعبه افتتاح کننده', 'شماره شبای حساب',
        'کد نوع حساب', 'نوع حساب', 'کد ارز', 'نوع ارز',
        'تاریخ افتتاح حساب', 'کد وضعیت حساب', 'وضعیت حساب',
        'وضعیت اتصال به پایانه یا درگاه پرداخت', 'گردش حساب از تاریخ',
        'گردش حساب تا تاریخ', 'تاریخ اخذ گزارش', 'ساعت اخذ گزارش',
        'کد نوع مشتری', 'نوع مشتری', 'نام', 'نام خانوادگی',
        'شماره ملی', 'شناسه ملی', 'شناسه اختصاصی اتباع خارجی', 'شناسه شهاب',
        'حق برداشت', 'قدرالسهم', 'کد نوع ارتباط با حساب', 'نوع ارتباط با حساب',
        'تاریخ شروع رابطه', 'تاریخ پایان رابطه'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for account in accounts:
            for rel in account['relationships']:
                customer = rel['customer']

                # Determine ID column names
                # Individuals carry شماره ملی, legal entities شناسه ملی, foreigners a FIDA code
                code = customer['customer_type_code']
                national_id_col = customer['national_id'] if code == 1 else ''
                national_id_label = customer['national_id'] if code == 3 else ''
                fida_col = customer['fida_code']

                row = {
                    'کد بانک': account['bank_code'],
                    'نام بانک': account['bank_name'],
                    'کد شعبه افتتاح کننده': account['branch_code'],
                    'شماره شبای حساب': account['sheba'],
                    'کد نوع حساب': account['account_type_code'],
                    'نوع حساب': account['account_type'],
                    'کد ارز': account['currency_code'],
                    'نوع ارز': account['currency_name'],
                    'تاریخ افتتاح حساب': account['opening_date'],
                    'کد وضعیت حساب': account['status_code'],
                    'وضعیت حساب': account['status'],
                    'وضعیت اتصال به پایانه یا درگاه پرداخت': account['terminal_connection'],
                    'گردش حساب از تاریخ': account['balance_from_date'],
                    'گردش حساب تا تاریخ': account['balance_to_date'],
                    'تاریخ اخذ گزارش': account['report_date'],
                    'ساعت اخذ گزارش': account['report_time'],
                    'کد نوع مشتری': customer['customer_type_code'],
                    'نوع مشتری': customer['customer_type'],
                    'نام': customer['first_name'],
                    'نام خانوادگی': customer['last_name'],
                    'شماره ملی': national_id_col,
                    'شناسه ملی': national_id_label,
                    'شناسه اختصاصی اتباع خارجی': fida_col,
                    'شناسه شهاب': customer['shab_id'],
                    'حق برداشت': 'دارد' if rel['has_withdrawal'] else 'ندارد',
                    'قدرالسهم': rel['share'],
                    'کد نوع ارتباط با حساب': rel['relationship_code'],
                    'نوع ارتباط با حساب': rel['relationship_type'],
                    'تاریخ شروع رابطه': rel['start_date'],
                    'تاریخ پایان رابطه': rel['end_date'],
                }

                writer.writerow(row)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate Iranian banking master accounts data')
    parser.add_argument('--accounts', type=int, default=180, help='Number of accounts to generate')
    parser.add_argument('--customers', type=int, default=150, help='Number of customers to generate')
    parser.add_argument('--output', type=str, default='accounts_master.csv', help='Output CSV file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')

    args = parser.parse_args()

    random.seed(args.seed)

    print(f"Generating {args.accounts} accounts with {args.customers} customers...")

    generator = AccountGenerator(num_accounts=args.accounts, num_customers=args.customers)
    accounts = generator.generate_accounts()

    write_accounts_csv(accounts, args.output)

    print(f"Successfully wrote {len(accounts)} accounts to {args.output}")

if __name__ == '__main__':
    main()
