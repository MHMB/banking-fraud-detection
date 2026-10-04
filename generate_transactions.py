#!/usr/bin/env python3
"""
Generate Transaction Data for Iranian Banking Fraud Detection Scenarios

Each scenario plants one fraud typology inside realistic background activity
(salaries, purchases, rent, cash, B2B invoices). The fraud is deliberately
hidden: neutral descriptions, amounts that overlap legitimate traffic, and
fraud actors that also do normal business.

Outputs per scenario directory:
  transactions.csv  - the bank-side view (no labels)
  ground_truth.csv  - transaction_id, role for every planted fraud transaction
"""

import csv
import os
import random
from collections import defaultdict
from dataclasses import dataclass

INDIVIDUAL, FOREIGN, COMPANY = "حقيقي ايراني", "حقيقي اتباع خارجي", "حقوقي"

REPORTING_THRESHOLD = 50_000_000  # cash reporting threshold assumed by the scenarios (IRR)
SATNA_MIN = 150_000_000           # interbank transfers at/above this go through SATNA, below through PAYA

INTERNET, MOBILE, BRANCH, ATM = "اینترنت‌بانک", "موبایل‌بانک", "شعبه", "ATM"
CASH_IN, CASH_OUT, INTERNAL, PAYA, SATNA = "واریز نقدی", "برداشت نقدی", "انتقال داخلی", "پایا", "ساتنا"

BASE_DATE = "14030101"  # a Wednesday; offset % 7 == 2 is Friday


@dataclass(frozen=True)
class Account:
    sheba: str
    bank_code: str
    branch_code: str
    status: str
    customer_type: str
    customer_name: str
    shab_id: str
    opening_date: str


# ---------------------------------------------------------------- Jalali dates

def is_leap(year: int) -> bool:
    return year % 33 in (1, 5, 9, 13, 17, 22, 26, 30)


def month_len(year: int, month: int) -> int:
    if month <= 6:
        return 31
    if month <= 11:
        return 30
    return 30 if is_leap(year) else 29


def add_days(date: str, days: int) -> str:
    """Add (possibly negative) days to a Solar Hijri YYYYMMDD date."""
    y, m, d = int(date[:4]), int(date[4:6]), int(date[6:]) + days
    while d > month_len(y, m):
        d -= month_len(y, m)
        m, y = (1, y + 1) if m == 12 else (m + 1, y)
    while d < 1:
        m, y = (12, y - 1) if m == 1 else (m - 1, y)
        d += month_len(y, m)
    return f"{y}{m:02d}{d:02d}"


def rnd(x: float, unit: int) -> int:
    """Round to a multiple of unit (people and companies move round amounts)."""
    return max(unit, int(round(x / unit)) * unit)


# ---------------------------------------------------------------- generator

class Generator:
    def __init__(self, accounts, scenario: str, seed: int):
        self.rng = random.Random(f"{seed}-{scenario}")
        self.scenario = scenario
        self.free = [a for a in accounts if a.status == 'باز']
        self.actors, self.owners = [], set()
        self.tx, self.truth, self.ids = [], [], set()

    def pick(self, n, kind=None, where=None, prefer=None):
        """Pick n distinct active accounts of distinct customers as scenario actors."""
        pool = [a for a in self.free
                if a.shab_id not in self.owners
                and (kind is None or a.customer_type == kind)
                and (where is None or where(a))]
        if prefer and sum(map(prefer, pool)) >= n:
            pool = [a for a in pool if prefer(a)]
        if len(pool) < n:
            raise ValueError(f"scenario {self.scenario}: need {n} accounts ({kind}), only {len(pool)}")
        chosen = self.rng.sample(pool, n)
        for a in chosen:
            self.free.remove(a)
            self.owners.add(a.shab_id)
        self.actors += chosen
        return chosen

    @staticmethod
    def biz(day: int) -> int:
        """Branches and PAYA/SATNA do not operate on Friday."""
        return day + 1 if day % 7 == 2 else day

    def time(self, lo=8, hi=20) -> str:
        r = self.rng
        return f"{r.randint(lo, hi):02d}{r.randint(0, 59):02d}{r.randint(0, 59):02d}"

    def add(self, sender, receiver, amount, day, description="", time=None, channel=None, role=None):
        """sender=None is a cash deposit, receiver=None a cash withdrawal."""
        assert (sender or receiver) and sender != receiver
        if sender is None:
            kind = CASH_IN
        elif receiver is None:
            kind = CASH_OUT
        elif sender.bank_code == receiver.bank_code:
            kind = INTERNAL
        else:
            kind = SATNA if amount >= SATNA_MIN else PAYA
        cash = kind in (CASH_IN, CASH_OUT)
        if channel is None:
            channel = BRANCH if cash or amount >= SATNA_MIN and self.rng.random() < 0.5 \
                else self.rng.choice([INTERNET, MOBILE, MOBILE])
        if channel == BRANCH or kind in (PAYA, SATNA):
            day = self.biz(day)
        if time is None:
            time = self.time(8, 13) if channel == BRANCH else self.time(7, 23)

        while (tid := f"TXN{self.scenario}{self.rng.randint(10**7, 10**8 - 1)}") in self.ids:
            pass
        self.ids.add(tid)
        self.tx.append({
            'transaction_id': tid,
            'date': add_days(BASE_DATE, day),
            'time': time,
            'sender_sheba': sender.sheba if sender else '',
            'receiver_sheba': receiver.sheba if receiver else '',
            'amount': amount,
            'currency': 'IRR',
            'type': kind,
            'description': description,
            'reference': str(self.rng.randint(10**11, 10**12 - 1)),
            'channel': channel,
            'status': 'completed',
        })
        if role:
            self.truth.append((tid, role))
        return day

    # ------------------------------------------------------------ background

    def add_noise(self, n: int, days: int, quiet=()):
        """Legitimate activity over the whole scenario window.

        Fraud actors (except `quiet` ones, e.g. dormant victims) take part too,
        so they are not isolated in the graph.
        """
        r = self.rng
        actors = [a for a in self.actors if a not in quiet]
        people = [a for a in actors if a.customer_type != COMPANY] + \
            r.sample([a for a in self.free if a.customer_type != COMPANY], 45)
        firms = [a for a in actors if a.customer_type == COMPANY] + \
            r.sample([a for a in self.free if a.customer_type == COMPANY], 8)
        merchants = r.sample(firms, 4)
        employers = r.sample(firms, 3)
        payroll = [(e, p, rnd(r.uniform(22e6, 49.5e6), 100_000))
                   for e in employers for p in r.sample(people, 4)]

        kinds = ["purchase", "p2p", "salary", "cash_out", "cash_in", "b2b", "big"]
        for _ in range(n):
            kind = r.choices(kinds, weights=[30, 27, 14, 10, 8, 8, 3])[0]
            day = r.randrange(days)
            p = r.choice(people)
            if kind == "purchase":
                self.add(p, r.choice(merchants), r.randint(200_000, 15_000_000), day,
                         r.choice(["خرید کالا", "پرداخت قبض", "شهریه", "خرید اینترنتی", ""]))
            elif kind == "p2p":
                q = r.choice([x for x in people if x != p])
                amount = rnd(min(60e6, r.lognormvariate(15.5, 1.0)), 100_000)
                self.add(p, q, amount, day, r.choice(["", "", "انتقال وجه", "قرض", "اجاره", "بابت بدهی"]))
            elif kind == "salary":
                e, emp, amount = r.choice(payroll)
                month_end = 28 + 30 * r.randrange(max(1, days // 30)) + r.randint(0, 2)
                self.add(e, emp, amount, min(month_end, days - 1), "حقوق و دستمزد", channel=INTERNET)
            elif kind == "cash_out":
                if r.random() < 0.6:
                    self.add(p, None, r.choice([500_000, 1_000_000, 2_000_000]), day, channel=ATM)
                else:
                    self.add(p, None, rnd(r.uniform(5e6, 45e6), 1_000_000), day)
            elif kind == "cash_in":
                depositor = r.choice(people + merchants)
                self.add(None, depositor, rnd(r.uniform(2e6, 49e6), 100_000), day)
            elif kind == "b2b":
                a, b = r.sample(firms, 2)
                amount = min(2e9, max(50e6, r.lognormvariate(19.6, 0.8)))  # median ~325M, tail past 1B
                self.add(a, b, rnd(amount, 1_000_000), day,
                         r.choice([f"بابت فاکتور {r.randint(100, 999)}", "تسویه قرارداد", "خرید مواد اولیه"]))
            else:
                q = r.choice([x for x in people if x != p])
                self.add(p, q, rnd(r.uniform(150e6, 600e6), 10_000_000), day,
                         r.choice(["خرید خودرو", "ودیعه مسکن", ""]))

    # ------------------------------------------------------------ output

    def write(self, out_dir: str):
        self.tx.sort(key=lambda t: (t['date'], t['time']))
        for t in self.tx:  # sanity: valid dates, no self-loops
            y, m, d = int(t['date'][:4]), int(t['date'][4:6]), int(t['date'][6:])
            assert 1 <= m <= 12 and 1 <= d <= month_len(y, m), t
            assert t['sender_sheba'] != t['receiver_sheba'], t
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "transactions.csv"), 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=list(self.tx[0]))
            w.writeheader()
            w.writerows(self.tx)
        with open(os.path.join(out_dir, "ground_truth.csv"), 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['transaction_id', 'role'])
            w.writerows(self.truth)


# ---------------------------------------------------------------- scenarios

def scenario_01(g: Generator):
    """Simple layering: cash in at A, A->B->C->D, cash out at D. Three rounds."""
    A, = g.pick(1, INDIVIDUAL, where=lambda a: a.opening_date >= "14010101")  # recently opened
    B, C, D = g.pick(3, INDIVIDUAL)
    for start, cash in ((0, 45_000_000), (9, 48_500_000), (19, 42_000_000)):
        day = g.add(None, A, cash, g.biz(start), time=g.time(8, 9), role="placement")
        g.add(A, B, cash - 500_000, day, time=g.time(10, 21), role="layering")
        for i, (s, r) in enumerate(((B, C), (C, D)), start=2):
            day = g.biz(day + 1)
            g.add(s, r, cash - i * 500_000, day, role="layering")
        g.add(D, None, cash - 5_000_000, g.biz(day + 1), role="integration")
    g.add_noise(120, 35)


def scenario_02(g: Generator):
    """Structuring: smurfs deposit cash just below the threshold, forward to an aggregator."""
    agg, out = g.pick(2)
    smurfs = g.pick(9, INDIVIDUAL)
    total = 0
    for i in range(15):
        s = smurfs[i % len(smurfs)]
        day = g.biz(i // 2)
        amount = g.rng.randrange(430, 496) * 100_000  # 43.0M - 49.5M
        g.add(None, s, amount, day, time=g.time(8, 10), role="structured_deposit")
        g.add(s, agg, amount, day, time=g.time(11, 22), role="funnel_transfer")
        total += amount
    g.add(agg, out, rnd(total * 0.96, 1_000_000), g.biz(11), role="consolidation")
    g.add_noise(150, 35)


def scenario_03(g: Generator):
    """Shell companies round-tripping funds A->B->C->A on vague service invoices."""
    a, b, c = g.pick(3, COMPANY)
    day, invoice = 0, g.rng.randint(100, 400)
    for _ in range(4):
        amount = g.rng.randrange(420, 560) * 1_000_000
        for s, r, service in ((a, b, "خدمات مشاوره‌ای"), (b, c, "خدمات مدیریتی"), (c, a, "خدمات بازرگانی")):
            day = g.biz(day + g.rng.randint(1, 3))
            invoice += g.rng.randint(1, 4)
            g.add(s, r, amount, day, f"بابت فاکتور {invoice} - {service}", role="round_trip")
            amount = rnd(amount * g.rng.uniform(0.93, 0.97), 1_000_000)
        day += g.rng.randint(3, 6)
    g.add_noise(120, 45)


def scenario_04(g: Generator):
    """Terrorist financing: many small donations -> charity -> NGO -> foreign national."""
    is_ngo = lambda a: any(w in a.customer_name for w in ("موسسه", "سازمان"))
    charity, ngo = g.pick(2, COMPANY, prefer=is_ngo)
    foreign, = g.pick(1, FOREIGN)
    donors = g.pick(50, where=lambda a: a.customer_type != COMPANY)

    donations = []
    for donor in donors:
        for _ in range(g.rng.randint(1, 3)):
            day = g.rng.randrange(60)
            amount = g.rng.choice([1, 2, 2, 3, 3, 5]) * 1_000_000
            g.add(donor, charity, amount, day, g.rng.choice(["کمک خیریه", "نذر", ""]), role="donation")
            donations.append((day, amount))
    for first, last, tranche_day in ((0, 31, 31), (31, 60, 63)):
        collected = sum(a for d, a in donations if first <= d < last)
        day = g.add(charity, ngo, rnd(collected * 0.95, 1_000_000), tranche_day,
                    "کمک به پروژه‌های حمایتی", role="aggregation")
        g.add(ngo, foreign, rnd(collected * 0.95 * 0.9, 1_000_000), g.biz(day + 2), role="foreign_transfer")
    g.add_noise(250, 68)


def scenario_05(g: Generator):
    """Account takeover: retiree's steady pension pattern, then night-time drain via mobile."""
    victim, = g.pick(1, INDIVIDUAL, where=lambda a: a.opening_date < "13950101")
    fund, = g.pick(1, COMPANY)
    mule, = g.pick(1, where=lambda a: a.opening_date >= "14010101")
    beneficiary, = g.pick(1)
    shops = g.pick(3, COMPANY)

    for month in range(6):
        payday = month * 30 + g.rng.randint(0, 1)
        g.add(fund, victim, 25_000_000, payday, "حقوق بازنشستگی", time=g.time(7, 8), channel=INTERNET)
        for _ in range(g.rng.randint(2, 3)):
            g.add(victim, g.rng.choice(shops), g.rng.randint(1_500_000, 6_000_000),
                  payday + g.rng.randint(2, 25), g.rng.choice(["خرید کالا", "پرداخت قبض"]))
        g.add(victim, None, g.rng.choice([1_000_000, 2_000_000]), payday + g.rng.randint(1, 5), channel=ATM)

    day = g.add(victim, mule, 500_000_000, 180, time=g.time(1, 4), channel=MOBILE, role="takeover_transfer")
    for amount, gap in ((200_000_000, 1), (180_000_000, 2), (150_000_000, 1)):
        day = g.add(victim, beneficiary, amount, day + gap, time=g.time(0, 5), channel=MOBILE, role="drain")
    g.add_noise(150, 186)


def scenario_06(g: Generator):
    """Trade-based ML: inflated import payments routed via a broker that keeps ~15%."""
    importer, broker = g.pick(2, COMPANY)
    exporter, = g.pick(1, FOREIGN)
    proforma = g.rng.randint(1000, 5000)
    for cycle in range(5):
        proforma += g.rng.randint(3, 40)
        amount = g.rng.randrange(900, 1200) * 1_000_000
        day = g.add(importer, broker, amount, cycle * 20 + g.rng.randint(0, 3),
                    f"واردات کالا - پروفرما {proforma}", role="inflated_invoice")
        g.add(broker, exporter, rnd(amount * g.rng.uniform(0.84, 0.86), 1_000_000),
              g.biz(day + g.rng.randint(1, 3)), f"بابت پروفرما {proforma}", role="pass_through")
    g.add_noise(150, 90)


def scenario_07(g: Generator):
    """Insider fraud: dormant old accounts at one branch drained at the counter to shared mules."""
    eligible = defaultdict(int)
    for a in g.free:
        if a.customer_type == INDIVIDUAL and a.opening_date < "13980101":
            eligible[(a.bank_code, a.branch_code)] += 1
    branch = max(eligible, key=eligible.get)
    victims = g.pick(min(8, eligible[branch]), INDIVIDUAL,
                     where=lambda a: (a.bank_code, a.branch_code) == branch and a.opening_date < "13980101")
    mules = g.pick(4)
    for i, victim in enumerate(victims):
        amount = g.rng.randrange(50, 200) * 1_000_000
        mule = g.rng.choice(mules)
        day = g.add(victim, mule, amount, i * 3 + g.rng.randint(0, 1), channel=BRANCH, role="unauthorized_transfer")
        g.add(mule, None, rnd(amount * g.rng.uniform(0.85, 0.95), 1_000_000),
              g.biz(day + g.rng.randint(1, 2)), role="cash_out")
    g.add_noise(120, 35, quiet=victims)  # victims stay dormant outside the fraud


def scenario_08(g: Generator):
    """Circular payments: 18-account ring back to the originator, ~5% kept per hop, plus side paths."""
    ring = g.pick(18)
    origin = ring[0]
    amount, day = 1_000_000_000, 0
    for i in range(len(ring)):
        day = g.biz(day + g.rng.randint(1, 4))
        amount = rnd(amount * g.rng.uniform(0.94, 0.96), 100_000)
        g.add(ring[i], ring[(i + 1) % len(ring)], amount, day, role="ring_hop")
    for i in range(3):  # split from the originator, reconverge further along the ring
        day = g.add(origin, ring[5 + i], 200_000_000, i * 15 + g.rng.randint(0, 2), role="side_path")
        g.add(ring[5 + i], ring[11 + i], rnd(200_000_000 * g.rng.uniform(0.94, 0.96), 100_000),
              g.biz(day + g.rng.randint(1, 3)), role="side_path")
    g.add_noise(200, 55)


SCENARIOS = {
    '01': scenario_01, '02': scenario_02, '03': scenario_03, '04': scenario_04,
    '05': scenario_05, '06': scenario_06, '07': scenario_07, '08': scenario_08,
}


def load_accounts(accounts_file: str):
    """Load accounts (primary owner row per Sheba) from the master CSV."""
    accounts = {}
    with open(accounts_file, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            accounts.setdefault(row['شماره شبای حساب'], Account(
                sheba=row['شماره شبای حساب'],
                bank_code=row['کد بانک'],
                branch_code=row['کد شعبه افتتاح کننده'],
                status=row['وضعیت حساب'],
                customer_type=row['نوع مشتری'],
                customer_name=f"{row['نام']} {row['نام خانوادگی']}".strip(),
                shab_id=row['شناسه شهاب'],
                opening_date=row['تاریخ افتتاح حساب'],
            ))
    return list(accounts.values())


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate transaction data for fraud detection scenarios')
    parser.add_argument('--scenario', required=True, help="Scenario number (01-08) or 'all'")
    parser.add_argument('--accounts', default='accounts_master.csv', help='Master accounts CSV file')
    parser.add_argument('--output', help='Output directory (default scenario_XX; ignored with all)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    accounts = load_accounts(args.accounts)
    numbers = list(SCENARIOS) if args.scenario == 'all' else [args.scenario]
    for num in numbers:
        if num not in SCENARIOS:
            parser.error(f"invalid scenario '{num}', must be 01-08 or all")
        g = Generator(accounts, num, args.seed)
        SCENARIOS[num](g)
        out = args.output if args.output and args.scenario != 'all' else f"scenario_{num}"
        g.write(out)
        print(f"scenario {num}: {len(g.tx)} transactions ({len(g.truth)} planted) -> {out}")


if __name__ == '__main__':
    main()
