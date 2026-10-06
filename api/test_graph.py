"""Checks the path algorithms against the planted ground truth (no Neo4j needed).

Run: python -m pytest api  (or: python api/test_graph.py)
"""
import csv
import glob
import os

from graph import CASH, Tx, day_number, find_scatter_gather, relationships, scatter_gather_for

ROOT = os.path.join(os.path.dirname(__file__), "..")


def load():
    txs, truth = [], {}
    for path in sorted(glob.glob(os.path.join(ROOT, "scenario_*", "transactions.csv"))):
        scenario = os.path.basename(os.path.dirname(path))
        with open(path, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                txs.append(Tx(r["transaction_id"], r["date"], r["time"], r["sender_sheba"] or None,
                              r["receiver_sheba"] or None, int(r["amount"]), r["type"], r["channel"],
                              r["description"], scenario))
        with open(os.path.join(os.path.dirname(path), "ground_truth.csv"), encoding="utf-8-sig") as f:
            truth.update({r["transaction_id"]: (scenario, r["role"]) for r in csv.DictReader(f)})
    return txs, truth


TXS, TRUTH = load()


def planted(scenario, role):
    return sorted((t for t in TXS if TRUTH.get(t.id) == (scenario, role)), key=lambda t: t.ts)


def test_day_number():
    assert day_number("14030101") - day_number("14021229") == 1   # 1402 is not a leap year
    assert day_number("14040101") - day_number("14030101") == 366  # 1403 is
    assert day_number("14030701") - day_number("14030631") == 1


def test_scatter_gather_scenario_09():
    scatter, gather = planted("scenario_09", "scatter"), planted("scenario_09", "gather")
    source, target = scatter[0].src, gather[0].dst
    as_source = [p for p in scatter_gather_for(TXS, source) if p["target"] == target]
    assert as_source and as_source[0]["role"] == "source" and as_source[0]["branch_count"] == 7
    found = {t["id"] for b in as_source[0]["branches"] for t in b["transactions"]}
    assert found == {i for i, (s, _) in TRUTH.items() if s == "scenario_09"}
    assert any(p["role"] == "target" and p["source"] == source for p in scatter_gather_for(TXS, target))
    mule = scatter[0].dst
    assert any(p["role"] == "intermediary" for p in scatter_gather_for(TXS, mule))


def test_scatter_gather_cash_source_scenario_02():
    aggregator = planted("scenario_02", "consolidation")[0].src
    hits = [p for p in scatter_gather_for(TXS, aggregator) if p["source"] == CASH and p["role"] == "target"]
    assert hits and hits[0]["branch_count"] == 9  # 9 smurfs


def test_relationship_follows_time_order():
    hops = planted("scenario_08", "ring_hop")
    origin, far = hops[0].src, hops[9].dst
    pair, = relationships(TXS, [origin, far])
    assert pair["related"] and pair["a_to_b"] and pair["b_to_a"]
    for path in (pair["a_to_b"], pair["b_to_a"]):
        stamps = [t["date"] + t["time"] for t in path["transactions"]]
        assert stamps == sorted(stamps)
        assert path["transactions"][0]["from"] in (origin, far)


def test_no_relationship_when_money_left_before_it_arrived():
    txs = [Tx("1", "14030105", "100000", "A", "B", 100),
           Tx("2", "14030103", "100000", "B", "C", 100)]  # B paid C two days BEFORE A paid B
    pair, = relationships(txs, ["A", "C"])
    assert not pair["related"]
    txs.append(Tx("3", "14030106", "100000", "B", "C", 100))
    pair, = relationships(txs, ["A", "C"])
    assert pair["a_to_b"]["intermediaries"] == ["B"] and pair["b_to_a"] is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    pats = find_scatter_gather(TXS)
    print(len(pats), "scatter-gather patterns in whole graph; branch counts:",
          sorted((len(b) for _, _, b in pats), reverse=True)[:15])
