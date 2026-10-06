#!/usr/bin/env python3
"""Regenerate every figure used by fraud_detection_report.md.

Charts come from the scenario CSVs; the neo4j_graph.png images are the drawn
results of the detection queries in queries.py, run against a live Neo4j
(bash setup.sh first). Also writes stats.json with the numbers quoted in the report.

Usage: python report_assets/generate_assets.py
"""
import csv
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "output")]
from neo4j_helper import query  # noqa: E402
from queries import QUERIES     # noqa: E402

BG, FG, GRID = "#1a1a2e", "#ffffff", "#3a3a4e"
TEAL, PINK, BLUE, GREY, AMBER = "#00d4aa", "#e84393", "#0984e3", "#55596a", "#fdcb6e"
TITLES = {
    "01": "Simple Layering", "02": "Structuring (Smurfing)", "03": "Shell Company Network",
    "04": "Terrorist Financing", "05": "Account Takeover", "06": "Trade-Based ML",
    "07": "Insider Fraud", "08": "Circular Payments", "09": "Scatter-Gather",
}
CHANNELS = {"اینترنت‌بانک": "Internet bank", "موبایل‌بانک": "Mobile bank", "شعبه": "Branch", "ATM": "ATM"}

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "savefig.dpi": 150,
    "savefig.bbox": "tight", "text.color": FG, "axes.labelcolor": FG, "axes.edgecolor": GRID,
    "xtick.color": FG, "ytick.color": FG, "font.family": "DejaVu Sans", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False, "legend.facecolor": "#16213e",
    "legend.edgecolor": GRID,
})


def short(sheba):
    return f"..{sheba[-4:]}"


def millions(amount):
    return f"{amount / 1e9:.2f}B" if amount >= 1e9 else f"{amount / 1e6:.1f}M"


def load(n):
    folder = os.path.join(ROOT, f"scenario_{n}")
    with open(os.path.join(folder, "transactions.csv"), encoding="utf-8-sig") as f:
        txs = list(csv.DictReader(f))
    with open(os.path.join(folder, "ground_truth.csv"), encoding="utf-8-sig") as f:
        truth = {r["transaction_id"]: r["role"] for r in csv.DictReader(f)}
    for t in txs:
        t["amount"] = int(t["amount"])
        t["planted"] = t["transaction_id"] in truth
    return txs, truth


def save(fig, *path):
    out = os.path.join(HERE, *path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out)
    plt.close(fig)


# ------------------------------------------------------------ per-scenario charts

def flow_graph(n, txs):
    """Planted flow in colour over the legitimate activity of the same accounts."""
    planted = [t for t in txs if t["planted"]]
    actors = {t[k] for t in planted for k in ("sender_sheba", "receiver_sheba") if t[k]}
    g = nx.MultiDiGraph()
    for t in txs:
        s, r = t["sender_sheba"] or "cash in", t["receiver_sheba"] or "cash out"
        if t["planted"] or ((s in actors or r in actors) and t["sender_sheba"] and t["receiver_sheba"]):
            g.add_edge(s, r, planted=t["planted"], amount=t["amount"])
    pos = nx.spring_layout(g, k=1.6 / max(1, len(g)) ** 0.5, iterations=200, seed=7,
                           weight=None)
    fig, ax = plt.subplots(figsize=(14, 10))
    legit = [(u, v) for u, v, d in g.edges(data=True) if not d["planted"]]
    fraud = [(u, v, d) for u, v, d in g.edges(data=True) if d["planted"]]
    nx.draw_networkx_edges(g, pos, edgelist=legit, edge_color=GREY, alpha=0.35, width=0.7,
                           arrowsize=7, ax=ax, node_size=300)
    top = max(d["amount"] for _, _, d in fraud)
    nx.draw_networkx_edges(g, pos, edgelist=[(u, v) for u, v, _ in fraud], edge_color=PINK,
                           width=[1.2 + 3 * d["amount"] / top for _, _, d in fraud],
                           arrowsize=14, ax=ax, node_size=420, connectionstyle="arc3,rad=0.12")
    cash = [x for x in g if x.startswith("cash")]
    others = [x for x in g if x not in actors and x not in cash]
    nx.draw_networkx_nodes(g, pos, nodelist=others, node_color="#2d3436", edgecolors=GREY, node_size=220, ax=ax)
    nx.draw_networkx_nodes(g, pos, nodelist=list(actors), node_color=BLUE, edgecolors=FG, linewidths=1.5,
                           node_size=420, ax=ax)
    nx.draw_networkx_nodes(g, pos, nodelist=cash, node_color=AMBER, edgecolors=FG, node_shape="s",
                           node_size=420, ax=ax)
    labels = {x: (x if x in cash else short(x)) for x in list(actors) + cash}
    if len(labels) <= 30:
        nx.draw_networkx_labels(g, pos, labels, font_size=7, font_color=FG, font_weight="bold", ax=ax)
    handles = [plt.Line2D([0], [0], color=PINK, lw=3, label="Planted fraud flow"),
               plt.Line2D([0], [0], color=GREY, lw=1, label="Legitimate flow of the same accounts"),
               plt.Line2D([0], [0], marker="o", color=BG, markerfacecolor=BLUE, markersize=11, label="Fraud-involved account"),
               plt.Line2D([0], [0], marker="o", color=BG, markerfacecolor="#2d3436", markeredgecolor=GREY, markersize=9, label="Other account"),
               plt.Line2D([0], [0], marker="s", color=BG, markerfacecolor=AMBER, markersize=10, label="Cash")]
    ax.legend(handles=handles, loc="upper left", fontsize=9)
    ax.text(0.99, 0.01, f"Transactions: {len(txs)}\nPlanted: {len(planted)}\n"
            f"Planted volume: {millions(sum(t['amount'] for t in planted))} IRR",
            transform=ax.transAxes, ha="right", va="bottom", family="monospace", fontsize=9,
            bbox=dict(boxstyle="round", facecolor="#16213e", edgecolor=GRID))
    ax.set_title(f"Scenario {n}: {TITLES[n]} — planted flow (labels from ground truth)", fontsize=14, fontweight="bold")
    ax.axis("off")
    save(fig, f"scenario_{n}", "transaction_flow_graph.png")


def amount_distribution(n, txs):
    """Shows how far planted amounts hide inside legitimate ones."""
    fig, ax = plt.subplots(figsize=(11, 5.5))
    lo, hi = min(t["amount"] for t in txs), max(t["amount"] for t in txs)
    bins = [lo * (hi / lo) ** (i / 30) for i in range(31)]
    ax.hist([[t["amount"] for t in txs if not t["planted"]], [t["amount"] for t in txs if t["planted"]]],
            bins=bins, stacked=True, color=[TEAL, PINK], edgecolor=BG, label=["Legitimate", "Planted fraud"])
    ax.set_xscale("log")
    ax.set_xlabel("Amount (IRR, log scale)")
    ax.set_ylabel("Transactions")
    ax.set_title(f"Scenario {n}: amount distribution", fontweight="bold")
    ax.legend()
    save(fig, f"scenario_{n}", "amount_distribution.png")


def channel_distribution(n, txs):
    fig, ax = plt.subplots(figsize=(9, 5))
    names = list(CHANNELS)
    legit = [sum(1 for t in txs if t["channel"] == c and not t["planted"]) for c in names]
    fraud = [sum(1 for t in txs if t["channel"] == c and t["planted"]) for c in names]
    x = [CHANNELS[c] for c in names]
    ax.bar(x, legit, color=TEAL, label="Legitimate")
    ax.bar(x, fraud, bottom=legit, color=PINK, label="Planted fraud")
    for i, (a, b) in enumerate(zip(legit, fraud)):
        ax.text(i, a + b + 1, f"{a + b}", ha="center", fontweight="bold")
    ax.set_ylabel("Transactions")
    ax.set_title(f"Scenario {n}: channel distribution", fontweight="bold")
    ax.legend()
    save(fig, f"scenario_{n}", "channel_distribution.png")


# ------------------------------------------------------------ Neo4j query results

def walk(value, on_path):
    """Query rows hold paths as [node, rel, node, ...] lists, possibly nested in collect()."""
    if isinstance(value, list):
        if value and isinstance(value[0], dict) and len(value) % 2 == 1 and len(value) >= 3 \
                and all(isinstance(v, dict) for v in value):
            on_path(value[::2])
        else:
            for v in value:
                walk(v, on_path)


def node_key(node):
    return node.get("transaction_id") or node.get("sheba") or node.get("shab_id")


def query_graph(n, rows, truth):
    """Draw what the detection query returned, in Neo4j Browser colours. Returns the score."""
    g = nx.DiGraph()

    def on_path(nodes):
        for a, b in zip(nodes, nodes[1:]):
            g.add_node(node_key(a), **a)
            g.add_node(node_key(b), **b)
            g.add_edge(node_key(a), node_key(b))

    for row in rows:
        for value in row.values():
            walk(value, on_path)

    found = {k for k, d in g.nodes(data=True) if "transaction_id" in d}
    fig, ax = plt.subplots(figsize=(13, 10), facecolor="black")
    ax.set_facecolor("black")
    if len(g):
        pos = nx.spring_layout(g, k=1.4 / len(g) ** 0.5, iterations=150, seed=3)
        tx = [k for k in g if k in found]
        acct = [k for k in g if k not in found]
        nx.draw_networkx_edges(g, pos, edge_color="#a5abb6", arrowsize=10, width=1, ax=ax, node_size=500)
        nx.draw_networkx_nodes(g, pos, nodelist=acct, node_color="#c990c0", edgecolors="#b261a5", node_size=650, ax=ax)
        nx.draw_networkx_nodes(g, pos, nodelist=tx, node_color="#f4d9b0", edgecolors="#c9a676", node_size=520, ax=ax)
        if len(g) <= 60:
            nx.draw_networkx_labels(g, pos, {k: short(k) for k in acct}, font_size=6, font_color="white", ax=ax)
            nx.draw_networkx_labels(g, pos, {k: millions(g.nodes[k]["amount"]) for k in tx}, font_size=6,
                                    font_color="#2a2c34", ax=ax)
    handles = [plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#c990c0", markersize=11, label="Account"),
               plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#f4d9b0", markersize=11, label="Transaction")]
    ax.legend(handles=handles, loc="upper left", facecolor="black", edgecolor="#444", labelcolor="white")
    ax.set_title(f"Scenario {n}: result of the detection query ({len(rows)} rows)", color="white", fontweight="bold")
    ax.axis("off")
    fig.savefig(os.path.join(HERE, f"scenario_{n}", "neo4j_graph.png"), facecolor="black")
    plt.close(fig)

    hits = len(found & set(truth))
    missed = sorted({truth[i] for i in set(truth) - found})
    return {"returned_tx": len(found), "true_positive": hits, "false_positive": len(found) - hits,
            "planted": len(truth), "precision": round(hits / len(found), 2) if found else None,
            "recall": round(hits / len(truth), 2), "missed_roles": missed}


def full_graph():
    rows = query("MATCH (n)-[r]->(m) WITH n, r, m, rand() AS x ORDER BY x LIMIT 220 "
                 "RETURN labels(n)[0] AS a, elementId(n) AS ai, type(r) AS t, labels(m)[0] AS b, elementId(m) AS bi")
    colors = {"Account": "#c990c0", "Transaction": "#f4d9b0", "Customer": "#57c7e3", "Bank": "#f79767"}
    g = nx.DiGraph()
    for r in rows:
        g.add_node(r["ai"], label=r["a"])
        g.add_node(r["bi"], label=r["b"])
        g.add_edge(r["ai"], r["bi"])
    fig, ax = plt.subplots(figsize=(13, 10), facecolor="black")
    ax.set_facecolor("black")
    pos = nx.spring_layout(g, k=1.2 / len(g) ** 0.5, iterations=120, seed=5)
    nx.draw_networkx_edges(g, pos, edge_color="#a5abb6", arrowsize=7, width=0.7, ax=ax, node_size=150)
    nx.draw_networkx_nodes(g, pos, node_color=[colors[d["label"]] for _, d in g.nodes(data=True)], node_size=150, ax=ax)
    ax.legend(handles=[plt.Line2D([0], [0], marker="o", color="black", markerfacecolor=c, markersize=11, label=l)
                       for l, c in colors.items()], loc="upper left", facecolor="black", edgecolor="#444", labelcolor="white")
    ax.set_title(f"Random sample of the graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} relationships",
                 color="white", fontweight="bold")
    ax.axis("off")
    fig.savefig(os.path.join(HERE, "overview", "neo4j_full_graph.png"), facecolor="black")
    plt.close(fig)


# ------------------------------------------------------------ overview charts

def overview(stats):
    numbers = sorted(stats["scenarios"])
    fig, ax = plt.subplots(figsize=(11, 5.5))
    legit = [stats["scenarios"][n]["transactions"] - stats["scenarios"][n]["planted"] for n in numbers]
    fraud = [stats["scenarios"][n]["planted"] for n in numbers]
    ax.bar(numbers, legit, color=TEAL, label="Legitimate (noise)")
    ax.bar(numbers, fraud, bottom=legit, color=PINK, label="Planted fraud")
    for i, (a, b) in enumerate(zip(legit, fraud)):
        ax.text(i, a + b + 4, f"{b}/{a + b}", ha="center", fontweight="bold", fontsize=9)
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Transactions")
    ax.set_title("Planted fraud vs legitimate transactions per scenario", fontweight="bold")
    ax.legend()
    save(fig, "overview", "volume_comparison_chart.png")

    checks = stats["validation"]
    fig, ax = plt.subplots(figsize=(11, 6))
    names = list(checks)
    values = [checks[k] for k in names]
    counts = {"Accounts", "Customers", "Transactions", "Cash (one-sided) tx"}
    bars = ax.barh(names, values, color=[TEAL if (k in counts or checks[k] == 0) else AMBER for k in names])
    for bar, k in zip(bars, names):
        ok = k in counts or checks[k] == 0
        ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"[{'PASS' if ok else 'WARN'}] {checks[k]}", va="center", fontweight="bold",
                color=TEAL if ok else AMBER)
    ax.set_xlim(0, max(values) * 1.18)
    ax.set_title("Data Validation Summary", fontweight="bold", fontsize=15)
    save(fig, "overview", "data_validation_chart.png")


def validate(all_tx):
    with open(os.path.join(ROOT, "accounts_master.csv"), encoding="utf-8-sig") as f:
        master = list(csv.DictReader(f))
    shebas = {r["شماره شبای حساب"] for r in master}
    ids = [t["transaction_id"] for t in all_tx]
    return {
        "Accounts": len(shebas),
        "Customers": len({r["شناسه شهاب"] for r in master}),
        "Transactions": len(all_tx),
        "Cash (one-sided) tx": sum(1 for t in all_tx if not t["sender_sheba"] or not t["receiver_sheba"]),
        "No sender and no receiver": sum(1 for t in all_tx if not t["sender_sheba"] and not t["receiver_sheba"]),
        "Unknown Sheba": sum(1 for t in all_tx for k in ("sender_sheba", "receiver_sheba") if t[k] and t[k] not in shebas),
        "Duplicate IDs": len(ids) - len(set(ids)),
        "Zero / negative amounts": sum(1 for t in all_tx if t["amount"] <= 0),
        "Self transfers": sum(1 for t in all_tx if t["sender_sheba"] == t["receiver_sheba"]),
    }


def main():
    stats, all_tx = {"scenarios": {}}, []
    for folder in sorted(glob.glob(os.path.join(ROOT, "scenario_*"))):
        n = folder[-2:]
        txs, truth = load(n)
        all_tx += txs
        flow_graph(n, txs)
        amount_distribution(n, txs)
        channel_distribution(n, txs)
        detection = query_graph(n, query(QUERIES[n]), truth)
        roles = {}
        for role in truth.values():
            roles[role] = roles.get(role, 0) + 1
        stats["scenarios"][n] = {
            "title": TITLES[n], "transactions": len(txs), "planted": len(truth), "roles": roles,
            "volume": sum(t["amount"] for t in txs),
            "planted_volume": sum(t["amount"] for t in txs if t["planted"]),
            "first_date": txs[0]["date"], "last_date": txs[-1]["date"], "detection": detection,
        }
        print(n, detection)
    stats["validation"] = validate(all_tx)
    stats["graph"] = {r["label"]: r["n"] for r in query(
        "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS n")}
    stats["graph"].update({r["t"]: r["n"] for r in query("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS n")})
    full_graph()
    overview(stats)
    with open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: stats[k] for k in ("validation", "graph")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
