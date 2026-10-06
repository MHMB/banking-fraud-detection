"""Path analysis over bank transfers. Pure functions, no database access.

Every path is time-ordered: a hop can only use money that has already arrived.
"""

from collections import defaultdict
from dataclasses import dataclass, asdict
from functools import lru_cache
from typing import Optional

CASH = "CASH"  # pseudo-source for cash deposits (they have no sender account)


@dataclass(frozen=True)
class Tx:
    id: str
    date: str               # Solar Hijri YYYYMMDD
    time: str               # HHMMSS
    src: Optional[str]      # None for a cash deposit
    dst: Optional[str]      # None for a cash withdrawal
    amount: int
    type: str = ""
    channel: str = ""
    description: str = ""
    scenario: str = ""

    @property
    def ts(self) -> str:
        return self.date + self.time

    @property
    def day(self) -> int:
        return day_number(self.date)


@lru_cache(maxsize=None)
def _days_before_year(year: int) -> int:
    return sum(366 if y % 33 in (1, 5, 9, 13, 17, 22, 26, 30) else 365 for y in range(1300, year))


@lru_cache(maxsize=None)
def day_number(date: str) -> int:
    """Solar Hijri date -> running day count, so dates can be subtracted."""
    y, m, d = int(date[:4]), int(date[4:6]), int(date[6:])
    return _days_before_year(y) + (m - 1) * 31 - max(0, m - 7) + d


def hop(t: Tx) -> dict:
    d = asdict(t)
    d["from"], d["to"] = d.pop("src") or CASH, d.pop("dst")
    return d


# ------------------------------------------------------------ relationship

def earliest_paths(txs, source: str) -> dict:
    """Fewest-hop time-ordered path from `source` to every reachable account.

    One pass over the transfers in time order: when a transfer leaves an account
    that money from `source` has already reached, its receiver becomes reachable.
    Returns {account: [Tx, ...]}.
    """
    best = {source: (0, None)}  # account -> (hops, linked list of (tx, previous))
    for t in sorted((t for t in txs if t.src and t.dst), key=lambda t: t.ts):
        if t.src in best and t.dst != source:
            hops = best[t.src][0] + 1
            if t.dst not in best or hops < best[t.dst][0]:
                best[t.dst] = (hops, (t, best[t.src][1]))
    paths = {}
    for account, (_, node) in best.items():
        path = []
        while node:
            path.append(node[0])
            node = node[1]
        paths[account] = path[::-1]
    del paths[source]
    return paths


def relationships(txs, shebas: list) -> list:
    """For every pair of the given shebas: can money flow a->b or b->a, and how."""
    reach = {s: earliest_paths(txs, s) for s in shebas}

    def describe(path):
        return path and {"hops": len(path), "intermediaries": [t.dst for t in path[:-1]],
                         "first_date": path[0].date, "last_date": path[-1].date,
                         "transactions": [hop(t) for t in path]}

    result = []
    for i, a in enumerate(shebas):
        for b in shebas[i + 1:]:
            ab, ba = reach[a].get(b), reach[b].get(a)
            result.append({"a": a, "b": b, "related": bool(ab or ba),
                           "a_to_b": describe(ab), "b_to_a": describe(ba)})
    return result


# ------------------------------------------------------------ scatter-gather

def find_scatter_gather(txs, min_branches=2, max_hops=3, window_days=30, min_ratio=0.8) -> list:
    """All scatter-gather patterns: a source (account or cash) whose money travels
    over >= min_branches separate branches and is collected by one target.

    A branch is a time-ordered chain source -> 1..max_hops intermediaries -> target
    where each account forwards between min_ratio and 100% of what it received,
    all inside window_days. Branches of one pattern share no intermediary.
    """
    # ponytail: searches from every account in memory, fine for thousands of
    # transfers; for millions, start from the queried sheba and push down to the DB.
    out = defaultdict(list)
    for t in txs:
        if t.dst:
            out[t.src or CASH].append(t)

    patterns = []
    for source in list(out):
        by_target = defaultdict(list)

        def walk(path):
            last = path[-1]
            if len(path) >= 2:
                by_target[last.dst].append(path)
            if last.dst == source or len(path) > max_hops:
                return
            seen = {t.dst for t in path}
            for nxt in out[last.dst]:
                if (nxt.ts > last.ts and nxt.dst not in seen
                        and nxt.day - path[0].day <= window_days
                        and min_ratio * last.amount <= nxt.amount <= last.amount):
                    walk(path + [nxt])

        for first in out[source]:
            walk([first])

        for target, paths in by_target.items():
            branches, used = [], set()
            for path in sorted(paths, key=lambda p: (len(p), p[-1].ts)):
                mids = {t.dst for t in path[:-1]}
                if not mids & used:
                    used |= mids
                    branches.append(path)
            if len(branches) >= min_branches:
                patterns.append((source, target, branches))
    return patterns


def describe_pattern(source, target, branches, sheba=None) -> dict:
    scattered = sum(p[0].amount for p in branches)
    gathered = sum(p[-1].amount for p in branches)
    first = min((p[0] for p in branches), key=lambda t: t.ts)
    last = max((p[-1] for p in branches), key=lambda t: t.ts)
    mids = {t.dst for p in branches for t in p[:-1]}
    roles = [r for r, hit in (("source", sheba == source), ("target", sheba == target),
                              ("intermediary", sheba in mids)) if hit]
    return {
        "role": roles and "_and_".join(roles),
        "source": source, "source_kind": "cash" if source == CASH else "account",
        "target": target,
        "branch_count": len(branches),
        "scattered_amount": scattered, "gathered_amount": gathered,
        "retained_pct": round(100 * (1 - gathered / scattered), 2),
        "first_date": first.date, "last_date": last.date,
        "duration_days": last.day - first.day,
        "branches": [{"intermediaries": [t.dst for t in p[:-1]],
                      "transactions": [hop(t) for t in p]} for p in branches],
    }


def scatter_gather_for(txs, sheba: str, **params) -> list:
    """Scatter-gather patterns in which `sheba` is source, target or intermediary."""
    found = [describe_pattern(s, t, b, sheba) for s, t, b in find_scatter_gather(txs, **params)]
    return sorted((p for p in found if p["role"]), key=lambda p: -p["branch_count"])
