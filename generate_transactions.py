#!/usr/bin/env python3
"""
Generate Transaction Data for Iranian Banking Fraud Detection Scenarios
Creates scenario-specific transaction files with fraudulent and legitimate patterns
"""

import csv
import random
import json
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Transaction Channels
CHANNELS = [
    "شبکه",           # Online banking
    "شعبه",           # Branch
    "ATM",            # ATM
    "موبایل",         # Mobile banking
    "تلفن‌بانک",      # Phone banking
]

# Transaction Types
TRANSACTION_TYPES = [
    "برداشت",         # Withdrawal
    "واریزت",         # Transfer
    "واریت واریزت",   # Wire transfer
    "واریز",          # Deposit
]

# Transaction Statuses
STATUSES = [
    "completed",      # Completed successfully
    "pending",        # Pending processing
    "failed",         # Failed transaction
    "rejected",       # Rejected by bank
]

# Currencies
CURRENCIES = ["IRR", "USD", "EUR"]

@dataclass
class Account:
    """Bank account information"""
    sheba: str
    bank_code: str
    account_type: str
    status: str
    customer_type: str
    customer_name: str
    branch_code: str

class ScenarioGenerator:
    """Base class for scenario transaction generation"""

    def __init__(self, accounts: List[Account], random_seed: int = 42):
        random.seed(random_seed)
        self.accounts = accounts
        self.accounts_by_sheba = {acc.sheba: acc for acc in accounts}
        self.transactions = []

    def get_active_accounts(self, count: int = None, bank_code: str = None) -> List[Account]:
        """Get random active accounts"""
        active = [acc for acc in self.accounts if acc.status == 'باز']

        if bank_code:
            active = [acc for acc in active if acc.bank_code == bank_code]

        if count:
            return random.sample(active, min(count, len(active)))
        return active

    def get_account_by_customer_name(self, name_pattern: str) -> List[Account]:
        """Find accounts with customer name matching pattern"""
        return [acc for acc in self.accounts if name_pattern in acc.customer_name]

    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"TXN{random.randint(1000000000, 9999999999)}"

    def add_transaction(
        self,
        sender_sheba: str,
        receiver_sheba: str,
        amount: int,
        date: str,
        time: str = None,
        currency: str = "IRR",
        txn_type: str = "واریزت",
        description: str = "",
        reference: str = "",
        channel: str = "شبکه",
        status: str = "completed"
    ):
        """Add a transaction to the list"""
        if time is None:
            time = f"{random.randint(8, 20):02d}{random.randint(0, 59):02d}{random.randint(0, 59):02d}"

        if not reference:
            reference = f"REF{random.randint(100000, 999999)}"

        self.transactions.append({
            'transaction_id': self.generate_transaction_id(),
            'date': date,
            'time': time,
            'sender_sheba': sender_sheba,
            'receiver_sheba': receiver_sheba,
            'amount': amount,
            'currency': currency,
            'type': txn_type,
            'description': description,
            'reference': reference,
            'channel': channel,
            'status': status
        })

    def add_legitimate_transactions(self, num_transactions: int, start_date: str):
        """Add realistic legitimate transactions"""
        active_accounts = self.get_active_accounts(count=50)

        for i in range(num_transactions):
            sender = random.choice(active_accounts)
            receiver = random.choice([acc for acc in active_accounts if acc.sheba != sender.sheba])

            # Legitimate transaction types
            txn_type = random.choices(
                ["واریزت", "برداشت", "واریز"],
                weights=[0.6, 0.3, 0.1],
                k=1
            )[0]

            # Realistic amounts
            if txn_type == "برداشت":
                amount = random.randint(500000, 10000000)  # 500K to 10M
            elif txn_type == "واریز":
                amount = random.randint(5000000, 50000000)  # 5M to 50M
            else:  # Transfer
                amount = random.randint(100000, 20000000)  # 100K to 20M

            # Date progression
            day_offset = random.randint(0, 30)
            date = self.increment_date(start_date, day_offset)

            channel = random.choice(CHANNELS)
            description = random.choice([
                "انتقال وجه به حساب",
                "پرداخت قبض",
                "خرید از فروشگاه",
                "برداشت وجه",
                "واریز حقوق",
            ])

            if txn_type == "برداشت":
                self.add_transaction(
                    sender_sheba=sender.sheba,
                    receiver_sheba=sender.sheba,  # Withdrawal uses same account
                    amount=amount,
                    date=date,
                    txn_type=txn_type,
                    description=description,
                    channel=channel,
                    status="completed"
                )
            elif txn_type == "واریز":
                # Deposit
                self.add_transaction(
                    sender_sheba=sender.sheba,
                    receiver_sheba=sender.sheba,
                    amount=amount,
                    date=date,
                    txn_type=txn_type,
                    description=description,
                    channel=channel,
                    status="completed"
                )
            else:
                # Transfer
                self.add_transaction(
                    sender_sheba=sender.sheba,
                    receiver_sheba=receiver.sheba,
                    amount=amount,
                    date=date,
                    txn_type=txn_type,
                    description=description,
                    channel=channel,
                    status="completed"
                )

    @staticmethod
    def increment_date(date: str, days: int) -> str:
        """Increment Solar Hijri date by given days"""
        # Simple implementation (not accurate for month/year boundaries)
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:8])

        day += days
        if day > 30:
            day -= 30
            month += 1
            if month > 12:
                month -= 12
                year += 1

        return f"{year}{month:02d}{day:02d}"

    def write_transactions(self, output_file: str):
        """Write transactions to CSV file"""
        fieldnames = [
            'transaction_id', 'date', 'time', 'sender_sheba', 'receiver_sheba',
            'amount', 'currency', 'type', 'description', 'reference',
            'channel', 'status'
        ]

        # Sort by date and time
        self.transactions.sort(key=lambda x: (x['date'], x['time']))

        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for txn in self.transactions:
                writer.writerow(txn)

class Scenario01Layering(ScenarioGenerator):
    """Scenario 01: Simple Layering (Money Laundering)"""

    def generate(self, base_date: str = "14030101"):
        # Get 4 active individual accounts
        accounts = self.get_active_accounts(count=10)
        individual_accounts = [acc for acc in accounts if acc.customer_type == 'حقيقي ايراني'][:4]

        if len(individual_accounts) < 4:
            individual_accounts = self.get_active_accounts(count=4)

        A, B, C, D = individual_accounts[:4]

        # Fraudulent layering transactions
        # Day 1: A deposits 45M IRR (cash at branch)
        self.add_transaction(
            sender_sheba=A.sheba,
            receiver_sheba=A.sheba,
            amount=45000000,
            date=base_date,
            time="091500",
            txn_type="واریز",
            description="واریز نقدی",
            channel="شعبه",
            status="completed"
        )

        # Day 1: A → B transfer 44.5M (online banking)
        self.add_transaction(
            sender_sheba=A.sheba,
            receiver_sheba=B.sheba,
            amount=44500000,
            date=base_date,
            time="103000",
            txn_type="واریزت",
            description="انتقال وجه",
            channel="شبکه",
            status="completed"
        )

        # Day 2: B → C transfer 44M (mobile)
        day2 = self.increment_date(base_date, 1)
        self.add_transaction(
            sender_sheba=B.sheba,
            receiver_sheba=C.sheba,
            amount=44000000,
            date=day2,
            time="141500",
            txn_type="واریزت",
            description="انتقال وجه",
            channel="موبایل",
            status="completed"
        )

        # Day 3: C → D transfer 43.5M (online)
        day3 = self.increment_date(base_date, 2)
        self.add_transaction(
            sender_sheba=C.sheba,
            receiver_sheba=D.sheba,
            amount=43500000,
            date=day3,
            time="110000",
            txn_type="واریزت",
            description="انتقال وجه",
            channel="شبکه",
            status="completed"
        )

        # Day 4: D withdraws 40M (cash at branch)
        day4 = self.increment_date(base_date, 3)
        self.add_transaction(
            sender_sheba=D.sheba,
            receiver_sheba=D.sheba,
            amount=40000000,
            date=day4,
            time="100000",
            txn_type="برداشت",
            description="برداشت وجه",
            channel="شعبه",
            status="completed"
        )

        # Add legitimate transactions
        self.add_legitimate_transactions(num_transactions=65, start_date=base_date)

class Scenario02Structuring(ScenarioGenerator):
    """Scenario 02: Structuring (Smurfing)"""

    def generate(self, base_date: str = "14030101"):
        # Get 1 primary aggregator account and 8-10 source accounts
        accounts = self.get_active_accounts(count=20)

        aggregator = accounts[0]
        source_accounts = accounts[1:10]

        # Structuring transactions: 15 transactions of 45M each (threshold: 50M)
        for i in range(15):
            source = source_accounts[i % len(source_accounts)]

            # Spread across 10 days
            day_offset = (i // 2)  # 1-2 transactions per day
            txn_date = self.increment_date(base_date, day_offset)

            # Random time between 9 AM and 5 PM
            time = f"{9 + random.randint(0, 8):02d}{random.randint(0, 59):02d}{random.randint(0, 59):02d}"

            # Some from same branch, some from different branches
            branch = source.branch_code if i < 8 else random.choice(["5692412", "1234567", "9876543"])

            self.add_transaction(
                sender_sheba=source.sheba,
                receiver_sheba=aggregator.sheba,
                amount=45000000,  # Just below 50M threshold
                date=txn_date,
                time=time,
                txn_type="واریزت",
                description=f"واریزت {i+1}",
                channel="شعبه",
                status="completed"
            )

        # Final consolidation to single outbound transfer
        consolidation_date = self.increment_date(base_date, 11)
        self.add_transaction(
            sender_sheba=aggregator.sheba,
            receiver_sheba=accounts[10].sheba,
            amount=650000000,  # 650M
            date=consolidation_date,
            time="110000",
            txn_type="واریت واریزت",
            description="تسویه حساب",
            channel="شبکه",
            status="completed"
        )

        # Add legitimate transactions
        self.add_legitimate_transactions(num_transactions=70, start_date=base_date)

class Scenario03ShellCompany(ScenarioGenerator):
    """Scenario 03: Shell Company Network"""

    def generate(self, base_date: str = "14030101"):
        # Get corporate accounts
        accounts = self.get_active_accounts(count=50)
        corporate_accounts = [acc for acc in accounts if acc.customer_type == 'حقوقی'][:3]

        if len(corporate_accounts) < 3:
            corporate_accounts = self.get_active_accounts(count=3)

        company_a, company_b, company_c = corporate_accounts

        # Cycle 1
        # Day 1: Company A → Company B: 500M
        self.add_transaction(
            sender_sheba=company_a.sheba,
            receiver_sheba=company_b.sheba,
            amount=500000000,
            date=base_date,
            txn_type="واریزت",
            description="فاکتور #INV-001 - خدمات مشاوره‌ای",
            channel="شبکه",
            status="completed"
        )

        # Day 3: Company B → Company C: 450M
        day3 = self.increment_date(base_date, 2)
        self.add_transaction(
            sender_sheba=company_b.sheba,
            receiver_sheba=company_c.sheba,
            amount=450000000,
            date=day3,
            txn_type="واریزت",
            description="فاکتور #INV-002 - خدمات مدیریتی",
            channel="شبکه",
            status="completed"
        )

        # Day 5: Company C → Company A: 480M
        day5 = self.increment_date(base_date, 4)
        self.add_transaction(
            sender_sheba=company_c.sheba,
            receiver_sheba=company_a.sheba,
            amount=480000000,
            date=day5,
            txn_type="واریزت",
            description="فاکتور #INV-003 - خدمات بازرگانی",
            channel="شبکه",
            status="completed"
        )

        # Cycle 2 (with variations)
        day10 = self.increment_date(base_date, 9)
        self.add_transaction(
            sender_sheba=company_a.sheba,
            receiver_sheba=company_b.sheba,
            amount=485000000,
            date=day10,
            txn_type="واریزت",
            description="فاکتور #INV-004 - خدمات مشاوره‌ای",
            channel="شبکه",
            status="completed"
        )

        day12 = self.increment_date(base_date, 11)
        self.add_transaction(
            sender_sheba=company_b.sheba,
            receiver_sheba=company_c.sheba,
            amount=440000000,
            date=day12,
            txn_type="واریزت",
            description="فاکتور #INV-005 - مشاوره مدیریت",
            channel="شبکه",
            status="completed"
        )

        day14 = self.increment_date(base_date, 13)
        self.add_transaction(
            sender_sheba=company_c.sheba,
            receiver_sheba=company_a.sheba,
            amount=475000000,
            date=day14,
            txn_type="واریزت",
            description="فاکتور #INV-006 - خدمات بازرگانی",
            channel="شبکه",
            status="completed"
        )

        # Add legitimate transactions
        self.add_legitimate_transactions(num_transactions=45, start_date=base_date)

class Scenario04TerroristFinancing(ScenarioGenerator):
    """Scenario 04: Terrorist Financing"""

    def generate(self, base_date: str = "14030101"):
        accounts = self.get_active_accounts(count=60)

        # 1 charity organization account
        charity = accounts[0]

        # 1 NGO account
        ngo = accounts[1]

        # 1 foreign entity account
        foreign_entity = accounts[2]

        # 50 donor accounts (individual + some foreign nationals)
        donor_accounts = accounts[3:53]

        # 50 donors: 1-5M each to charity (spread over 2 months)
        for i, donor in enumerate(donor_accounts):
            # Spread over 60 days
            day_offset = random.randint(0, 60)
            donor_date = self.increment_date(base_date, day_offset)

            amount = random.randint(1000000, 5000000)

            self.add_transaction(
                sender_sheba=donor.sheba,
                receiver_sheba=charity.sheba,
                amount=amount,
                date=donor_date,
                txn_type="واریزت",
                description="کمک خیریه",
                channel=random.choice(["شبکه", "موبایل", "شعبه"]),
                status="completed"
            )

        # Charity consolidates and transfers 200M to NGO
        consolidation_date = self.increment_date(base_date, 65)
        self.add_transaction(
            sender_sheba=charity.sheba,
            receiver_sheba=ngo.sheba,
            amount=200000000,
            date=consolidation_date,
            txn_type="واریزت",
            description="انتقال به سازمان غیردولتی",
            channel="شبکه",
            status="completed"
        )

        # NGO → Foreign entity: 180M IRR
        transfer_date = self.increment_date(base_date, 67)
        self.add_transaction(
            sender_sheba=ngo.sheba,
            receiver_sheba=foreign_entity.sheba,
            amount=180000000,
            date=transfer_date,
            txn_type="واریت واریزت",
            description="انتقال بین‌المللی",
            currency="IRR",
            channel="شبکه",
            status="completed"
        )

        # Add legitimate transactions
        self.add_legitimate_transactions(num_transactions=70, start_date=base_date)

class Scenario05AccountTakeover(ScenarioGenerator):
    """Scenario 05: Account Takeover + Fraud"""

    def generate(self, base_date: str = "14030101"):
        accounts = self.get_active_accounts(count=10)

        # Customer X: long-standing account (will be taken over)
        victim = accounts[0]

        # Customer Y: new suspicious account
        attacker_new = accounts[1]

        # Customer Z: offshore connection
        beneficiary = accounts[2]

        # Before takeover: normal activity (months 1-6)
        for month in range(6):
            payday = self.increment_date(base_date, month * 30)
            self.add_transaction(
                sender_sheba=victim.sheba,
                receiver_sheba=victim.sheba,
                amount=25000000,  # Monthly pension
                date=payday,
                time="080000",
                txn_type="واریز",
                description="واریز حقوق بازنشستگی",
                channel="شبکه",
                status="completed"
            )

            # Small living expenses
            expense_date = self.increment_date(payday, random.randint(2, 10))
            self.add_transaction(
                sender_sheba=victim.sheba,
                receiver_sheba=random.choice([a.sheba for a in accounts[3:6]]),
                amount=random.randint(2000000, 5000000),
                date=expense_date,
                txn_type="واریزت",
                description="خرید مخاز",
                channel="شبکه",
                status="completed"
            )

        # Takeover event: change contact info
        takeover_date = self.increment_date(base_date, 180)

        # Large transfer to new beneficiary
        self.add_transaction(
            sender_sheba=victim.sheba,
            receiver_sheba=attacker_new.sheba,
            amount=500000000,
            date=takeover_date,
            time="140000",
            txn_type="واریزت",
            description="انتقال وجه - تغییر اطلاعات تماس",
            channel="شبکه",
            status="completed"
        )

        # After takeover (months 7-9): rapid transfers
        after_date = self.increment_date(takeover_date, 1)

        # Transfer 1: 200M
        self.add_transaction(
            sender_sheba=victim.sheba,
            receiver_sheba=beneficiary.sheba,
            amount=200000000,
            date=after_date,
            time="100000",
            txn_type="واریزت",
            description="انتقال وجه",
            channel="شبکه",
            status="completed"
        )

        # Transfer 2: 180M
        after_date2 = self.increment_date(after_date, 2)
        self.add_transaction(
            sender_sheba=victim.sheba,
            receiver_sheba=beneficiary.sheba,
            amount=180000000,
            date=after_date2,
            time="110000",
            txn_type="واریزت",
            description="انتقال وجه",
            channel="شبکه",
            status="completed"
        )

        # Transfer 3: 150M
        after_date3 = self.increment_date(after_date2, 1)
        self.add_transaction(
            sender_sheba=victim.sheba,
            receiver_sheba=beneficiary.sheba,
            amount=150000000,
            date=after_date3,
            time="103000",
            txn_type="واریزت",
            description="انتقال وجه - تسویه حساب",
            channel="شبکه",
            status="completed"
        )

        # Add legitimate transactions
        self.add_legitimate_transactions(num_transactions=40, start_date=base_date)

class Scenario06TradeBasedML(ScenarioGenerator):
    """Scenario 06: Trade-Based Money Laundering"""

    def generate(self, base_date: str = "14030101"):
        accounts = self.get_active_accounts(count=50)

        # Company A: Iran importer
        importer = accounts[0]

        # Company B: UAE exporter (foreign national account)
        exporter = accounts[1] if accounts[1].customer_type == 'حقيقي اتباع خارجي' else accounts[2]

        # Company C: Intermediary in free zone
        intermediary = accounts[2]

        # Company D: Another shell company
        shell = accounts[3]

        # Multiple over-invoicing transactions over 3 months
        for cycle in range(5):
            # Calculate dates
            import_date = self.increment_date(base_date, cycle * 20)
            intermediary_date = self.increment_date(import_date, 2)
            export_date = self.increment_date(intermediary_date, 3)

            # Invoice amount: 1B IRR (showing as equivalent of 1M USD)
            invoice_amount = 1000000000

            # Actual value: 200M IRR (actual 200K USD)
            # Route: A → C → B
            # C charges 15% commission

            # A → C: 1B (over-invoiced amount)
            self.add_transaction(
                sender_sheba=importer.sheba,
                receiver_sheba=intermediary.sheba,
                amount=invoice_amount,
                date=import_date,
                txn_type="واریت واریزت",
                description=f"واردات الکترونیکی - فاکتور #{cycle+100}",
                channel="شبکه",
                status="completed"
            )

            # C → B: 850M (after 15% commission)
            commission = int(invoice_amount * 0.15)
            amount_to_exporter = invoice_amount - commission

            self.add_transaction(
                sender_sheba=intermediary.sheba,
                receiver_sheba=exporter.sheba,
                amount=amount_to_exporter,
                date=intermediary_date,
                txn_type="واریت واریزت",
                description=f"پرداخت فاکتور #{cycle+100} - کارمزد: 15%",
                channel="شبکه",
                status="completed"
            )

        # Add legitimate transactions
        self.add_legitimate_transactions(num_transactions=60, start_date=base_date)

class Scenario07InsiderFraud(ScenarioGenerator):
    """Scenario 07: Insider Fraud (Bank Employee)"""

    def generate(self, base_date: str = "14030101"):
        accounts = self.get_active_accounts(count=50)

        # Target accounts: dormant, elderly, deceased customers
        target_accounts = accounts[:12]

        # Beneficiary accounts controlled by employee
        beneficiary_accounts = accounts[12:17]

        # Manipulate target accounts
        for i, target in enumerate(target_accounts):
            # Dormant account reactivated
            fraud_date = self.increment_date(base_date, i * 3)

            # Large transfer out
            amount = random.randint(50000000, 200000000)

            self.add_transaction(
                sender_sheba=target.sheba,
                receiver_sheba=random.choice(beneficiary_accounts).sheba,
                amount=amount,
                date=fraud_date,
                time=f"{9 + i:02d}0000",
                txn_type="واریزت",
                description=f"برداشت وجه - شعبه {target.branch_code}",
                channel="شعبه",
                status="completed"
            )

            # Some accounts have email/phone changed (simulated with description)
            if i % 3 == 0:
                self.add_transaction(
                    sender_sheba=target.sheba,
                    receiver_sheba=target.sheba,
                    amount=0,
                    date=self.increment_date(fraud_date, -1),
                    time="090000",
                    txn_type="واریزت",
                    description="تغییر اطلاعات تماس - ایمیل و شماره موبایل",
                    channel="شعبه",
                    status="completed"
                )

        # Add legitimate transactions
        self.add_legitimate_transactions(num_transactions=35, start_date=base_date)

class Scenario08CircularPayments(ScenarioGenerator):
    """Scenario 08: Circular Payments (Complex Network)"""

    def generate(self, base_date: str = "14030101"):
        # Get 20 accounts for circular network
        accounts = self.get_active_accounts(count=30)

        # Create circular path: A → B → C ... → S → T → A
        network_accounts = accounts[:20]

        originator = network_accounts[0]
        final_amount = 1000000000  # 1B starting amount

        # Create circular flow with 15-18 hops
        current_amount = final_amount
        current_date = base_date
        current_account = originator

        for hop in range(18):
            if hop >= len(network_accounts) - 1:
                next_account = originator  # Return to originator
            else:
                next_account = network_accounts[hop + 1]

            # Extract commission at each hop
            commission = int(current_amount * 0.05)  # 5% commission
            next_amount = current_amount - commission

            # Random delay: 0-5 days
            delay = random.randint(0, 5)
            current_date = self.increment_date(current_date, delay)

            self.add_transaction(
                sender_sheba=current_account.sheba,
                receiver_sheba=next_account.sheba,
                amount=next_amount,
                date=current_date,
                time=f"{9 + random.randint(0, 8):02d}{random.randint(0, 59):02d}00",
                txn_type="واریزت",
                description=f"انتقال وجه - مرحله {hop+1}",
                channel=random.choice(["شبکه", "موبایل"]),
                status="completed"
            )

            current_amount = next_amount
            current_account = next_account

        # Add some parallel paths for obfuscation
        # Branch splits and reconverges
        for i in range(3):
            parallel_date = self.increment_date(base_date, i * 15)

            # Split from originator to 2 paths, then reconverge
            account1 = network_accounts[5 + i]
            account2 = network_accounts[10 + i]
            reconverge = network_accounts[15 + i]

            amount = 200000000

            # Path 1
            self.add_transaction(
                sender_sheba=originator.sheba,
                receiver_sheba=account1.sheba,
                amount=amount,
                date=parallel_date,
                txn_type="واریزت",
                description=f"مسیر موازی {i+1}-A",
                channel="شبکه",
                status="completed"
            )

            # Reconverge
            self.add_transaction(
                sender_sheba=account1.sheba,
                receiver_sheba=reconverge.sheba,
                amount=int(amount * 0.95),
                date=self.increment_date(parallel_date, random.randint(1, 3)),
                txn_type="واریزت",
                description=f"مسیر موازی {i+1}-B",
                channel="موبایل",
                status="completed"
            )

        # Add legitimate transactions
        self.add_legitimate_transactions(num_transactions=80, start_date=base_date)

def load_accounts(accounts_file: str) -> List[Account]:
    """Load accounts from master CSV file"""
    accounts = []
    sheba_set = set()

    with open(accounts_file, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            sheba = row['شماره شبای حساب']

            # Skip duplicate shebas (same account, different customers)
            if sheba in sheba_set:
                continue
            sheba_set.add(sheba)

            account = Account(
                sheba=sheba,
                bank_code=row['کد بانک'],
                account_type=row['نوع حساب'],
                status=row['وضعیت حساب'],
                customer_type=row['نوع مشتری'],
                customer_name=f"{row['نام']} {row['نام خانوادگی']}",
                branch_code=row['کد شعبه افتتاح کننده']
            )
            accounts.append(account)

    return accounts

def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Generate transaction data for fraud detection scenarios')
    parser.add_argument('--scenario', type=str, required=True, help='Scenario number (01-08)')
    parser.add_argument('--accounts', type=str, default='accounts_master.csv', help='Master accounts CSV file')
    parser.add_argument('--output', type=str, help='Output directory (will create scenario_XX/transactions.csv)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')

    args = parser.parse_args()

    # Load accounts
    print(f"Loading accounts from {args.accounts}...")
    accounts = load_accounts(args.accounts)
    print(f"Loaded {len(accounts)} unique accounts")

    # Determine output directory
    if args.output:
        output_dir = args.output
    else:
        output_dir = f"scenario_{args.scenario}"

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "transactions.csv")

    # Generate scenario-specific transactions
    scenario_class = {
        '01': Scenario01Layering,
        '02': Scenario02Structuring,
        '03': Scenario03ShellCompany,
        '04': Scenario04TerroristFinancing,
        '05': Scenario05AccountTakeover,
        '06': Scenario06TradeBasedML,
        '07': Scenario07InsiderFraud,
        '08': Scenario08CircularPayments,
    }.get(args.scenario)

    if not scenario_class:
        print(f"Error: Invalid scenario number '{args.scenario}'. Must be 01-08.")
        return

    print(f"Generating Scenario {args.scenario} transactions...")
    generator = scenario_class(accounts, random_seed=args.seed)
    generator.generate()

    # Write transactions
    generator.write_transactions(output_file)
    print(f"Wrote {len(generator.transactions)} transactions to {output_file}")

if __name__ == '__main__':
    main()
