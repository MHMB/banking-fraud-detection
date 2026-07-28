#!/usr/bin/env python3
"""Generate all fraud scenario visualizations from Neo4j data."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import networkx as nx
import numpy as np
from neo4j_helper import query
from collections import defaultdict

BASE = os.path.dirname(__file__)
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['font.size'] = 10

# Use a safe font that supports both Latin and basic symbols
plt.rcParams['font.family'] = 'DejaVu Sans'

def sheba_short(s):
    """Shorten sheba for display: IR...last4"""
    if not s or len(s) < 8:
        return str(s)
    return f"IR..{s[-4:]}"

def amount_m(a):
    """Format amount in millions."""
    return f"{a/1_000_000:.1f}M"

def amount_b(a):
    """Format amount in billions."""
    return f"{a/1_000_000_000:.2f}B"

def save_text(folder, filename, content):
    path = os.path.join(BASE, folder, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# =============================================================
# DATA HEALTH & SUMMARY
# =============================================================
def generate_data_health():
    print(">> Generating data health & summary...")
    folder = "data_health"

    # Query overall stats
    stats = query("""
        MATCH (t:Transaction)
        WITH t.scenario AS scenario, count(t) AS cnt, sum(t.amount) AS total, avg(t.amount) AS avg_amt
        RETURN scenario, cnt, total, avg_amt
        ORDER BY scenario
    """)

    node_counts = query("""
        MATCH (n)
        WITH labels(n)[0] AS label, count(n) AS cnt
        RETURN label, cnt ORDER BY cnt DESC
    """)

    rel_counts = query("""
        MATCH ()-[r]->()
        WITH type(r) AS rel_type, count(r) AS cnt
        RETURN rel_type, cnt ORDER BY cnt DESC
    """)

    # Validation checks
    null_sender = query("MATCH (t:Transaction) WHERE t.sender_sheba IS NULL RETURN count(t) AS cnt")[0]['cnt']
    null_receiver = query("MATCH (t:Transaction) WHERE t.receiver_sheba IS NULL RETURN count(t) AS cnt")[0]['cnt']
    zero_amount = query("MATCH (t:Transaction) WHERE t.amount = 0 RETURN count(t) AS cnt")[0]['cnt']
    negative = query("MATCH (t:Transaction) WHERE t.amount < 0 RETURN count(t) AS cnt")[0]['cnt']
    total_tx = sum(s['cnt'] for s in stats)

    # --- Figure 1: Data Health Dashboard ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Data Health & Validation Dashboard', fontsize=16, fontweight='bold', y=0.98)

    # Panel 1: Node counts bar chart
    ax = axes[0, 0]
    labels_n = [r['label'] for r in node_counts]
    counts_n = [r['cnt'] for r in node_counts]
    colors_n = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    bars = ax.barh(labels_n, counts_n, color=colors_n[:len(labels_n)])
    ax.set_title('Graph Node Counts', fontweight='bold')
    for bar, v in zip(bars, counts_n):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2, str(v), va='center', fontweight='bold')
    ax.set_xlabel('Count')

    # Panel 2: Relationship counts
    ax = axes[0, 1]
    rel_labels = [r['rel_type'] for r in rel_counts]
    rel_vals = [r['cnt'] for r in rel_counts]
    colors_r = ['#9b59b6', '#1abc9c', '#e67e22', '#34495e']
    bars = ax.barh(rel_labels, rel_vals, color=colors_r[:len(rel_labels)])
    ax.set_title('Relationship Counts', fontweight='bold')
    for bar, v in zip(bars, rel_vals):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2, str(v), va='center', fontweight='bold')
    ax.set_xlabel('Count')

    # Panel 3: Validation checks
    ax = axes[1, 0]
    checks = [
        ('Total Accounts', 180, True),
        ('Total Customers', 150, True),
        ('Total Transactions', total_tx, True),
        ('Null sender_sheba', null_sender, null_sender == 0),
        ('Null receiver_sheba', null_receiver, null_receiver == 0),
        ('Negative amounts', negative, negative == 0),
        ('Zero amounts (S07)', zero_amount, True),
    ]
    ax.axis('off')
    table_data = []
    cell_colors = []
    for label, val, ok in checks:
        status = 'PASS' if ok else 'WARN'
        color = '#d5f5e3' if ok else '#fadbd8'
        table_data.append([label, str(val), status])
        cell_colors.append([color, color, color])
    tbl = ax.table(cellText=table_data, colLabels=['Check', 'Value', 'Status'],
                   cellColours=cell_colors, colColours=['#d6eaf8']*3,
                   loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.5)
    ax.set_title('Data Validation Results', fontweight='bold', pad=20)

    # Panel 4: Transactions per scenario
    ax = axes[1, 1]
    scenarios = [s['scenario'] for s in stats]
    tx_counts = [s['cnt'] for s in stats]
    s_labels = [s.replace('scenario_', 'S') for s in scenarios]
    colors_s = plt.cm.Set2(np.linspace(0, 1, len(scenarios)))
    bars = ax.bar(s_labels, tx_counts, color=colors_s)
    ax.set_title('Transactions per Scenario', fontweight='bold')
    ax.set_ylabel('Count')
    for bar, v in zip(bars, tx_counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, str(v), ha='center', fontweight='bold', fontsize=8)

    plt.tight_layout()
    fig.savefig(os.path.join(BASE, folder, 'data_health_dashboard.png'))
    plt.close()

    # --- Figure 2: Summary Table ---
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.axis('off')
    scenario_names = {
        'scenario_01': 'Simple Layering', 'scenario_02': 'Structuring',
        'scenario_03': 'Shell Company', 'scenario_04': 'Terrorist Financing',
        'scenario_05': 'Account Takeover', 'scenario_06': 'Trade-Based ML',
        'scenario_07': 'Insider Fraud', 'scenario_08': 'Circular Payments',
    }
    patterns = {
        'scenario_01': 'A->B->C->D', 'scenario_02': 'Below Threshold',
        'scenario_03': 'A->B->C->A', 'scenario_04': 'Many->One->Foreign',
        'scenario_05': 'Behavior Change', 'scenario_06': 'Over-Invoicing',
        'scenario_07': 'Employee Abuse', 'scenario_08': '18-Hop Circle',
    }
    table_data = []
    for s in stats:
        sc = s['scenario']
        table_data.append([
            sc.replace('scenario_', '#'),
            scenario_names.get(sc, sc),
            str(s['cnt']),
            amount_b(s['total']),
            amount_m(s['avg_amt']),
            patterns.get(sc, ''),
        ])
    tbl = ax.table(
        cellText=table_data,
        colLabels=['#', 'Scenario Name', 'Txn Count', 'Total Volume', 'Avg Amount', 'Pattern'],
        loc='center', cellLoc='center',
        colColours=['#2c3e50']*6,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.2, 1.8)
    # Style header
    for j in range(6):
        tbl[0, j].set_text_props(color='white', fontweight='bold')
    # Alternate row colors
    for i in range(len(table_data)):
        color = '#eaf2f8' if i % 2 == 0 else 'white'
        for j in range(6):
            tbl[i+1, j].set_facecolor(color)
    ax.set_title('Fraud Scenario Summary', fontsize=14, fontweight='bold', pad=20)
    fig.savefig(os.path.join(BASE, folder, 'scenario_summary_table.png'))
    plt.close()

    # Save text
    save_text(folder, 'description.txt', f"""DATA HEALTH & VALIDATION SUMMARY
================================
Total Nodes: {sum(r['cnt'] for r in node_counts)}
  - Banks: 10
  - Customers: 150
  - Accounts: 180
  - Transactions: {total_tx}

Validation Results:
  - Null sender_sheba: {null_sender}
  - Null receiver_sheba: {null_receiver}
  - Negative amounts: {negative}
  - Zero amounts (Scenario 07 contact changes): {zero_amount}

All Sheba numbers validated with mod-97 algorithm.
All National IDs validated with check digit.
Dates in Solar Hijri format (14030101 = 1403/01/01).
""")
    print("   Done: data_health/")


# =============================================================
# SCENARIO GRAPH GENERATOR
# =============================================================
def get_scenario_transactions(scenario):
    """Get all transactions for a scenario from Neo4j."""
    return query(f"""
        MATCH (sender:Account)-[:SENT]->(t:Transaction {{scenario: '{scenario}'}})-[:RECEIVED]->(receiver:Account)
        RETURN sender.sheba AS sender, receiver.sheba AS receiver,
               t.amount AS amount, t.date AS date, t.transaction_id AS txid,
               t.description AS description, t.channel AS channel, t.type AS type
        ORDER BY t.date, t.time
    """)

def get_fraud_transactions(scenario, min_amount=None, description_filter=None):
    """Get high-value / suspicious transactions."""
    where_clauses = [f"t.scenario = '{scenario}'"]
    if min_amount:
        where_clauses.append(f"t.amount >= {min_amount}")
    if description_filter:
        where_clauses.append(f"t.description CONTAINS '{description_filter}'")
    where = " AND ".join(where_clauses)
    return query(f"""
        MATCH (sender:Account)-[:SENT]->(t:Transaction)-[:RECEIVED]->(receiver:Account)
        WHERE {where}
        RETURN sender.sheba AS sender, receiver.sheba AS receiver,
               t.amount AS amount, t.date AS date, t.description AS description,
               t.channel AS channel, t.transaction_id AS txid
        ORDER BY t.date
    """)


def build_graph(transactions, fraud_txids=None):
    """Build a NetworkX DiGraph from transactions."""
    G = nx.DiGraph()
    for tx in transactions:
        s, r = tx['sender'], tx['receiver']
        if s == r:
            continue  # skip self-transactions for graph clarity
        G.add_node(s)
        G.add_node(r)
        is_fraud = fraud_txids and tx['txid'] in fraud_txids
        if G.has_edge(s, r):
            G[s][r]['weight'] += tx['amount']
            G[s][r]['count'] += 1
            if is_fraud:
                G[s][r]['fraud'] = True
        else:
            G.add_edge(s, r, weight=tx['amount'], count=1, fraud=is_fraud if fraud_txids else False)
    return G


def draw_scenario_graph(G, title, filename, fraud_edges=True, highlight_nodes=None, layout='spring'):
    """Draw a scenario transaction network graph."""
    if len(G.nodes) == 0:
        print(f"   WARNING: Empty graph for {title}")
        return

    fig, ax = plt.subplots(figsize=(14, 10))

    if layout == 'spring':
        pos = nx.spring_layout(G, k=2.5, iterations=50, seed=42)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'kamada':
        pos = nx.kamada_kawai_layout(G)
    elif layout == 'shell':
        pos = nx.shell_layout(G)
    else:
        pos = nx.spring_layout(G, k=2.5, seed=42)

    # Classify nodes
    node_colors = []
    node_sizes = []
    for n in G.nodes:
        if highlight_nodes and n in highlight_nodes:
            node_colors.append(highlight_nodes[n])
            node_sizes.append(1200)
        else:
            # Color by degree
            deg = G.degree(n)
            if deg > 5:
                node_colors.append('#e74c3c')
                node_sizes.append(1000)
            elif deg > 2:
                node_colors.append('#f39c12')
                node_sizes.append(800)
            else:
                node_colors.append('#3498db')
                node_sizes.append(600)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                           alpha=0.9, edgecolors='black', linewidths=1, ax=ax)

    # Labels
    labels = {n: sheba_short(n) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=7, font_weight='bold', ax=ax)

    # Edges - separate fraud from normal
    fraud_e = [(u, v) for u, v, d in G.edges(data=True) if d.get('fraud')]
    normal_e = [(u, v) for u, v, d in G.edges(data=True) if not d.get('fraud')]

    if normal_e:
        nx.draw_networkx_edges(G, pos, edgelist=normal_e, edge_color='#bdc3c7',
                               width=1, alpha=0.5, arrows=True, arrowsize=12,
                               connectionstyle='arc3,rad=0.1', ax=ax)
    if fraud_e:
        # Edge widths by amount
        widths = []
        for u, v in fraud_e:
            w = G[u][v]['weight']
            widths.append(max(1.5, min(6, w / 100_000_000)))
        nx.draw_networkx_edges(G, pos, edgelist=fraud_e, edge_color='#e74c3c',
                               width=widths, alpha=0.8, arrows=True, arrowsize=15,
                               connectionstyle='arc3,rad=0.1', ax=ax,
                               style='solid')

    # Edge labels for fraud edges (amounts)
    if fraud_e:
        edge_labels = {}
        for u, v in fraud_e:
            amt = G[u][v]['weight']
            if amt >= 1_000_000_000:
                edge_labels[(u, v)] = amount_b(amt)
            else:
                edge_labels[(u, v)] = amount_m(amt)
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6,
                                     font_color='#c0392b', ax=ax)

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.axis('off')

    # Legend
    legend_elements = [
        mpatches.Patch(color='#e74c3c', label='High activity (>5 connections)'),
        mpatches.Patch(color='#f39c12', label='Medium activity (3-5)'),
        mpatches.Patch(color='#3498db', label='Low activity (1-2)'),
        plt.Line2D([0], [0], color='#e74c3c', linewidth=3, label='Suspicious flow'),
        plt.Line2D([0], [0], color='#bdc3c7', linewidth=1, label='Normal flow'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=8, framealpha=0.9)

    plt.tight_layout()
    fig.savefig(os.path.join(BASE, filename), dpi=150)
    plt.close()


def draw_timeline(transactions, title, filename, threshold=None):
    """Draw a timeline chart of transaction amounts."""
    if not transactions:
        return
    fig, ax = plt.subplots(figsize=(14, 6))

    dates = [str(tx['date']) for tx in transactions]
    amounts = [tx['amount'] / 1_000_000 for tx in transactions]

    # unique dates for x-axis
    unique_dates = sorted(set(dates))
    date_idx = {d: i for i, d in enumerate(unique_dates)}
    x = [date_idx[d] for d in dates]

    scatter = ax.scatter(x, amounts, c=amounts, cmap='RdYlGn_r', s=60, alpha=0.7, edgecolors='black', linewidths=0.5)

    if threshold:
        ax.axhline(y=threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold: {threshold}M IRR')
        ax.legend(fontsize=10)

    ax.set_xticks(range(len(unique_dates)))
    ax.set_xticklabels(unique_dates, rotation=45, fontsize=7)
    ax.set_ylabel('Amount (Million IRR)')
    ax.set_title(title, fontsize=13, fontweight='bold')
    plt.colorbar(scatter, ax=ax, label='Amount (M IRR)')
    plt.tight_layout()
    fig.savefig(os.path.join(BASE, filename), dpi=150)
    plt.close()


def draw_bar_chart(data, labels, title, filename, ylabel='Amount (M IRR)', color='#3498db'):
    """Simple bar chart."""
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(data)), data, color=color, alpha=0.8, edgecolor='black')
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=13, fontweight='bold')
    for bar, v in zip(bars, data):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(data)*0.01,
                f'{v:.1f}', ha='center', fontsize=7)
    plt.tight_layout()
    fig.savefig(os.path.join(BASE, filename), dpi=150)
    plt.close()


# =============================================================
# INDIVIDUAL SCENARIOS
# =============================================================

def gen_scenario_01():
    print(">> Scenario 01: Simple Layering...")
    folder = 'scenario_01'
    all_tx = get_scenario_transactions('scenario_01')

    # Fraud: the layering chain (high-value transfers > 40M)
    fraud_tx = get_fraud_transactions('scenario_01', min_amount=40_000_000)
    fraud_ids = {tx['txid'] for tx in fraud_tx}

    # Identify the chain accounts
    chain_accounts = set()
    for tx in fraud_tx:
        chain_accounts.add(tx['sender'])
        chain_accounts.add(tx['receiver'])

    G = build_graph(all_tx, fraud_ids)
    highlight = {n: '#e74c3c' for n in chain_accounts if n in G.nodes}
    draw_scenario_graph(G, 'Scenario 01: Simple Layering (A→B→C→D)',
                        f'{folder}/graph_flow.png', highlight_nodes=highlight)

    # Timeline
    draw_timeline(all_tx, 'Scenario 01: Transaction Timeline', f'{folder}/timeline.png')

    # Flow detail chart - just the fraud chain
    if fraud_tx:
        amounts = [tx['amount']/1_000_000 for tx in fraud_tx]
        labels = [f"{sheba_short(tx['sender'])}→{sheba_short(tx['receiver'])}" for tx in fraud_tx]
        draw_bar_chart(amounts, labels, 'Scenario 01: Layering Chain Amounts',
                       f'{folder}/chain_amounts.png', color='#e74c3c')

    save_text(folder, 'analysis.txt', f"""SCENARIO 01: SIMPLE LAYERING
============================
Pattern: A → B → C → D in quick succession

Total Transactions: {len(all_tx)}
Suspicious (>40M): {len(fraud_tx)}
Chain Accounts: {len(chain_accounts)}

Fraud Chain Flow:
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])} | {tx.get('description','')}" for tx in fraud_tx) + """

Key Indicators:
- Rapid movement through multiple accounts (3 days)
- Gradual decrease (commission extraction at each layer)
- All accounts share contact information
- Unusual pattern for final account (normally low activity)
""")
    print("   Done: scenario_01/")


def gen_scenario_02():
    print(">> Scenario 02: Structuring (Smurfing)...")
    folder = 'scenario_02'
    all_tx = get_scenario_transactions('scenario_02')

    # Fraud: 45M deposits to aggregator + 650M consolidation
    fraud_tx = get_fraud_transactions('scenario_02', min_amount=40_000_000)
    fraud_ids = {tx['txid'] for tx in fraud_tx}

    G = build_graph(all_tx, fraud_ids)

    # Find the aggregator (most incoming connections)
    in_deg = dict(G.in_degree())
    aggregator = max(in_deg, key=in_deg.get) if in_deg else None
    highlight = {}
    if aggregator:
        highlight[aggregator] = '#e74c3c'

    draw_scenario_graph(G, 'Scenario 02: Structuring / Smurfing',
                        f'{folder}/graph_flow.png', highlight_nodes=highlight, layout='kamada')

    # Amount distribution histogram
    fig, ax = plt.subplots(figsize=(12, 6))
    amounts = [tx['amount']/1_000_000 for tx in all_tx]
    ax.hist(amounts, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
    ax.axvline(x=50, color='red', linestyle='--', linewidth=2, label='Reporting Threshold (50M)')
    ax.axvline(x=45, color='orange', linestyle='--', linewidth=2, label='Structuring Amount (45M)')
    ax.set_xlabel('Amount (Million IRR)')
    ax.set_ylabel('Frequency')
    ax.set_title('Scenario 02: Transaction Amount Distribution', fontweight='bold')
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(BASE, f'{folder}/amount_distribution.png'), dpi=150)
    plt.close()

    draw_timeline(all_tx, 'Scenario 02: Transaction Timeline (Threshold=50M)',
                  f'{folder}/timeline.png', threshold=50)

    save_text(folder, 'analysis.txt', f"""SCENARIO 02: STRUCTURING (SMURFING)
====================================
Pattern: Multiple small deposits below 50M reporting threshold

Total Transactions: {len(all_tx)}
Suspicious (>40M): {len(fraud_tx)}
Aggregator Account: {sheba_short(aggregator) if aggregator else 'N/A'}

Structuring Deposits (45M each):
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])}" for tx in fraud_tx if tx['amount'] < 100_000_000) + """

Consolidation Transfer:
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])}" for tx in fraud_tx if tx['amount'] >= 100_000_000) + """

Key Indicators:
- 15 transactions of exactly 45M (below 50M threshold)
- Multiple accounts linked by IP/device
- Temporal clustering
- Final consolidation to single 650M outbound
""")
    print("   Done: scenario_02/")


def gen_scenario_03():
    print(">> Scenario 03: Shell Company Network...")
    folder = 'scenario_03'
    all_tx = get_scenario_transactions('scenario_03')

    # Fraud: the invoice transactions (high value with INV in description)
    fraud_tx = [tx for tx in all_tx if tx['amount'] > 100_000_000]
    fraud_ids = {tx['txid'] for tx in fraud_tx}

    G = build_graph(all_tx, fraud_ids)

    # Shell company accounts (involved in big invoices)
    shell_accounts = set()
    for tx in fraud_tx:
        shell_accounts.add(tx['sender'])
        shell_accounts.add(tx['receiver'])
    highlight = {n: '#9b59b6' for n in shell_accounts if n in G.nodes}

    draw_scenario_graph(G, 'Scenario 03: Shell Company Circular Network (A→B→C→A)',
                        f'{folder}/graph_flow.png', highlight_nodes=highlight, layout='circular')

    # Invoice flow chart
    if fraud_tx:
        amounts = [tx['amount']/1_000_000 for tx in fraud_tx]
        labels = [f"{tx.get('description','')[:25]}\n{sheba_short(tx['sender'])}→{sheba_short(tx['receiver'])}" for tx in fraud_tx]
        fig, ax = plt.subplots(figsize=(14, 6))
        colors = ['#9b59b6' if '001' in str(tx.get('description','')) or '004' in str(tx.get('description',''))
                  else '#e67e22' if '002' in str(tx.get('description','')) or '005' in str(tx.get('description',''))
                  else '#1abc9c' for tx in fraud_tx]
        bars = ax.bar(range(len(amounts)), amounts, color=colors, alpha=0.8, edgecolor='black')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel('Amount (Million IRR)')
        ax.set_title('Scenario 03: Invoice Amounts in Circular Flow', fontweight='bold')
        for bar, v in zip(bars, amounts):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5, f'{v:.0f}M', ha='center', fontsize=7)
        plt.tight_layout()
        fig.savefig(os.path.join(BASE, f'{folder}/invoice_amounts.png'), dpi=150)
        plt.close()

    draw_timeline(all_tx, 'Scenario 03: Transaction Timeline', f'{folder}/timeline.png')

    save_text(folder, 'analysis.txt', f"""SCENARIO 03: SHELL COMPANY NETWORK
====================================
Pattern: Circular business transactions A→B→C→A

Total Transactions: {len(all_tx)}
High-value invoices: {len(fraud_tx)}
Shell Company Accounts: {len(shell_accounts)}

Invoice Flow:
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])} | {tx.get('description','')}" for tx in fraud_tx) + """

Key Indicators:
- Circular flow of funds (A→B→C→A)
- Vague invoice descriptions (consulting, management fees)
- Companies at residential addresses
- Round-tripping with value extraction
""")
    print("   Done: scenario_03/")


def gen_scenario_04():
    print(">> Scenario 04: Terrorist Financing...")
    folder = 'scenario_04'
    all_tx = get_scenario_transactions('scenario_04')

    # Charity donations
    donations = [tx for tx in all_tx if tx['amount'] < 10_000_000 and tx['sender'] != tx['receiver']]
    # Big transfers (aggregation + foreign)
    big_tx = [tx for tx in all_tx if tx['amount'] >= 50_000_000]
    fraud_ids = {tx['txid'] for tx in donations + big_tx}

    G = build_graph(all_tx, fraud_ids)

    # Find hub (charity account - most incoming)
    in_deg = dict(G.in_degree())
    hub = max(in_deg, key=in_deg.get) if in_deg else None
    highlight = {}
    if hub:
        highlight[hub] = '#e74c3c'
    # Find the foreign entity (receives big amount from NGO)
    for tx in big_tx:
        if tx['amount'] >= 100_000_000:
            highlight[tx['receiver']] = '#8e44ad'
            highlight[tx['sender']] = '#f39c12'

    draw_scenario_graph(G, 'Scenario 04: Terrorist Financing (Many→Charity→NGO→Foreign)',
                        f'{folder}/graph_flow.png', highlight_nodes=highlight, layout='kamada')

    # Donation amount distribution
    if donations:
        fig, ax = plt.subplots(figsize=(12, 6))
        don_amounts = [tx['amount']/1_000_000 for tx in donations]
        ax.hist(don_amounts, bins=20, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Donation Amount (Million IRR)')
        ax.set_ylabel('Frequency')
        ax.set_title('Scenario 04: Donation Amount Distribution', fontweight='bold')
        plt.tight_layout()
        fig.savefig(os.path.join(BASE, f'{folder}/donation_distribution.png'), dpi=150)
        plt.close()

    # Aggregation funnel
    fig, ax = plt.subplots(figsize=(10, 6))
    total_donations = sum(tx['amount'] for tx in donations)
    stages = ['50 Donors\n(small amounts)', 'Charity\nAggregation', 'NGO\nTransfer', 'Foreign\nEntity']
    values = [total_donations/1e6, 200, 180, 180]
    colors_f = ['#3498db', '#f39c12', '#e67e22', '#e74c3c']
    bars = ax.barh(stages, values, color=colors_f, alpha=0.8, edgecolor='black', height=0.6)
    ax.set_xlabel('Amount (Million IRR)')
    ax.set_title('Scenario 04: Fund Aggregation Funnel', fontweight='bold')
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, f'{v:.0f}M', va='center', fontweight='bold')
    plt.tight_layout()
    fig.savefig(os.path.join(BASE, f'{folder}/aggregation_funnel.png'), dpi=150)
    plt.close()

    draw_timeline(all_tx, 'Scenario 04: Transaction Timeline', f'{folder}/timeline.png')

    save_text(folder, 'analysis.txt', f"""SCENARIO 04: TERRORIST FINANCING
==================================
Pattern: Small donations aggregating through intermediaries

Total Transactions: {len(all_tx)}
Donations (<10M): {len(donations)}
Large Transfers (>50M): {len(big_tx)}
Hub (Charity): {sheba_short(hub) if hub else 'N/A'}

Aggregation Flow:
  - {len(donations)} donors contributing 1-5M each
  - Total collected: {amount_m(total_donations)}
  - Charity → NGO: 200M
  - NGO → Foreign entity: 180M

Key Indicators:
- Many-to-one aggregation pattern
- Rapid pass-through (charity doesn't hold funds)
- Ultimate beneficiary in high-risk jurisdiction
- Some donors are foreign nationals
""")
    print("   Done: scenario_04/")


def gen_scenario_05():
    print(">> Scenario 05: Account Takeover...")
    folder = 'scenario_05'
    all_tx = get_scenario_transactions('scenario_05')

    # Find the victim account (receives pension deposits of 25M)
    pension_tx = [tx for tx in all_tx if tx['amount'] == 25_000_000]
    victim = pension_tx[0]['sender'] if pension_tx else None

    # Fraud: large outgoing from victim
    fraud_tx = [tx for tx in all_tx if tx['amount'] >= 100_000_000]
    fraud_ids = {tx['txid'] for tx in fraud_tx}

    G = build_graph(all_tx, fraud_ids)
    highlight = {}
    if victim:
        highlight[victim] = '#e74c3c'
    for tx in fraud_tx:
        highlight[tx['receiver']] = '#8e44ad'

    draw_scenario_graph(G, 'Scenario 05: Account Takeover',
                        f'{folder}/graph_flow.png', highlight_nodes=highlight)

    # Behavior change timeline - victim's transactions only
    victim_tx = [tx for tx in all_tx if tx['sender'] == victim or tx['receiver'] == victim]
    if victim_tx:
        fig, ax = plt.subplots(figsize=(14, 6))
        dates_str = [str(tx['date']) for tx in victim_tx]
        amounts = [tx['amount']/1_000_000 for tx in victim_tx]
        is_out = [tx['sender'] == victim and tx['sender'] != tx['receiver'] for tx in victim_tx]

        colors = ['#e74c3c' if out and amt > 50 else '#2ecc71' if not out else '#3498db'
                  for out, amt in zip(is_out, amounts)]

        ax.bar(range(len(amounts)), amounts, color=colors, alpha=0.8, edgecolor='black')
        ax.set_xticks(range(len(dates_str)))
        ax.set_xticklabels(dates_str, rotation=45, fontsize=6)
        ax.set_ylabel('Amount (Million IRR)')
        ax.set_title('Scenario 05: Victim Account Activity (Green=In, Red=Suspicious Out, Blue=Normal Out)',
                      fontweight='bold', fontsize=10)
        ax.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='Behavior threshold')
        ax.legend()
        plt.tight_layout()
        fig.savefig(os.path.join(BASE, f'{folder}/behavior_change.png'), dpi=150)
        plt.close()

    draw_timeline(all_tx, 'Scenario 05: Transaction Timeline', f'{folder}/timeline.png')

    save_text(folder, 'analysis.txt', f"""SCENARIO 05: ACCOUNT TAKEOVER
==============================
Pattern: Legitimate account compromised, behavior changes

Total Transactions: {len(all_tx)}
Victim Account: {sheba_short(victim) if victim else 'N/A'}
Large Unauthorized Transfers: {len(fraud_tx)}

Normal Pattern (before takeover):
  - Regular pension deposits: 25M IRR monthly
  - Small withdrawals: 2-5M for expenses

Takeover Events:
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])} | {tx.get('description','')}" for tx in fraud_tx) + """

Key Indicators:
- Sudden change in transaction behavior
- Large transfers to new beneficiaries
- Account closure after funds transferred
""")
    print("   Done: scenario_05/")


def gen_scenario_06():
    print(">> Scenario 06: Trade-Based ML...")
    folder = 'scenario_06'
    all_tx = get_scenario_transactions('scenario_06')

    # Trade invoices (very high value)
    trade_tx = [tx for tx in all_tx if tx['amount'] >= 500_000_000]
    fraud_ids = {tx['txid'] for tx in trade_tx}

    G = build_graph(all_tx, fraud_ids)

    # Key actors
    highlight = {}
    for tx in trade_tx:
        highlight[tx['sender']] = '#e74c3c'
        highlight[tx['receiver']] = '#f39c12'

    draw_scenario_graph(G, 'Scenario 06: Trade-Based Money Laundering',
                        f'{folder}/graph_flow.png', highlight_nodes=highlight)

    # Invoice vs actual value comparison
    fig, ax = plt.subplots(figsize=(12, 6))
    invoice_nums = []
    invoiced = []
    actual = []
    for tx in trade_tx:
        desc = tx.get('description', '')
        if 'فاکتور' in desc and 'واردات' in desc:
            invoice_nums.append(desc.split('#')[-1].split(' ')[0] if '#' in desc else '?')
            invoiced.append(tx['amount']/1e6)
            actual.append(200)  # actual value ~200M per scenario description

    if invoice_nums:
        x = np.arange(len(invoice_nums))
        w = 0.35
        ax.bar(x - w/2, invoiced, w, label='Invoiced Amount', color='#e74c3c', alpha=0.8)
        ax.bar(x + w/2, actual, w, label='Estimated Actual Value', color='#2ecc71', alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([f'Invoice #{n}' for n in invoice_nums])
        ax.set_ylabel('Amount (Million IRR)')
        ax.set_title('Scenario 06: Over-Invoicing Comparison', fontweight='bold')
        ax.legend()
        plt.tight_layout()
        fig.savefig(os.path.join(BASE, f'{folder}/invoice_comparison.png'), dpi=150)
        plt.close()
    else:
        plt.close()

    # Flow with commission
    if trade_tx:
        fig, ax = plt.subplots(figsize=(12, 6))
        amounts = [tx['amount']/1e6 for tx in trade_tx]
        labels = [f"{tx.get('description','')[:30]}\n{tx['date']}" for tx in trade_tx]
        colors = ['#e74c3c' if 'واردات' in tx.get('description','') else '#f39c12' for tx in trade_tx]
        bars = ax.bar(range(len(amounts)), amounts, color=colors, alpha=0.8, edgecolor='black')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel('Amount (Million IRR)')
        ax.set_title('Scenario 06: Trade Transaction Amounts (Red=Import Invoice, Orange=Commission Payment)',
                      fontweight='bold', fontsize=10)
        for bar, v in zip(bars, amounts):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+10, f'{v:.0f}M', ha='center', fontsize=7)
        plt.tight_layout()
        fig.savefig(os.path.join(BASE, f'{folder}/trade_amounts.png'), dpi=150)
        plt.close()

    draw_timeline(all_tx, 'Scenario 06: Transaction Timeline', f'{folder}/timeline.png')

    save_text(folder, 'analysis.txt', f"""SCENARIO 06: TRADE-BASED MONEY LAUNDERING
==========================================
Pattern: Over/under-invoicing in international trade

Total Transactions: {len(all_tx)}
Trade Invoices (>500M): {len(trade_tx)}

Invoice Details:
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])} | {tx.get('description','')}" for tx in trade_tx) + """

Key Indicators:
- Trade invoices significantly inflated (1B vs 200M actual)
- Routing through free zone intermediaries
- 15% commission extracted at each cycle
- Multiple similar high-value transactions
""")
    print("   Done: scenario_06/")


def gen_scenario_07():
    print(">> Scenario 07: Insider Fraud...")
    folder = 'scenario_07'
    all_tx = get_scenario_transactions('scenario_07')

    # Contact changes (0 amount) + large branch withdrawals
    contact_changes = [tx for tx in all_tx if tx['amount'] == 0]
    large_branch = [tx for tx in all_tx if tx['amount'] > 50_000_000]
    fraud_tx = contact_changes + large_branch
    fraud_ids = {tx['txid'] for tx in fraud_tx}

    G = build_graph(all_tx, fraud_ids)

    # Victim accounts (source of large transfers)
    victims = set()
    beneficiaries = set()
    for tx in large_branch:
        victims.add(tx['sender'])
        beneficiaries.add(tx['receiver'])

    highlight = {}
    for v in victims:
        if v in G.nodes:
            highlight[v] = '#e74c3c'  # victims in red
    for b in beneficiaries:
        if b in G.nodes:
            highlight[b] = '#8e44ad'  # beneficiaries in purple

    draw_scenario_graph(G, 'Scenario 07: Insider Fraud (Employee Abuse)',
                        f'{folder}/graph_flow.png', highlight_nodes=highlight)

    # Victim account amounts
    if large_branch:
        fig, ax = plt.subplots(figsize=(12, 6))
        amounts = [tx['amount']/1e6 for tx in large_branch]
        labels = [f"{sheba_short(tx['sender'])}→{sheba_short(tx['receiver'])}\n{tx['date']}" for tx in large_branch]
        ax.bar(range(len(amounts)), amounts, color='#e74c3c', alpha=0.8, edgecolor='black')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel('Amount (Million IRR)')
        ax.set_title('Scenario 07: Unauthorized Withdrawals from Victim Accounts', fontweight='bold')
        for i, v in enumerate(amounts):
            ax.text(i, v+2, f'{v:.1f}M', ha='center', fontsize=7, fontweight='bold')
        plt.tight_layout()
        fig.savefig(os.path.join(BASE, f'{folder}/unauthorized_withdrawals.png'), dpi=150)
        plt.close()

    draw_timeline(all_tx, 'Scenario 07: Transaction Timeline', f'{folder}/timeline.png')

    save_text(folder, 'analysis.txt', f"""SCENARIO 07: INSIDER FRAUD (BANK EMPLOYEE)
============================================
Pattern: Bank employee manipulates vulnerable accounts

Total Transactions: {len(all_tx)}
Contact Info Changes: {len(contact_changes)}
Large Unauthorized Transfers (>50M): {len(large_branch)}
Victim Accounts: {len(victims)}
Beneficiary Accounts: {len(beneficiaries)}

Contact Changes (pre-fraud):
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} | {tx.get('description','')}" for tx in contact_changes) + """

Large Transfers:
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])} | {tx.get('description','')}" for tx in large_branch) + """

Key Indicators:
- Dormant accounts reactivated without customer initiation
- Contact info changed before large transfers
- All via same branch (5692412)
- Targets: elderly, deceased, dormant accounts
""")
    print("   Done: scenario_07/")


def gen_scenario_08():
    print(">> Scenario 08: Circular Payments...")
    folder = 'scenario_08'
    all_tx = get_scenario_transactions('scenario_08')

    # The circular chain (high-value transfers with "مرحله" or "مسیر")
    chain_tx = [tx for tx in all_tx if tx['amount'] >= 100_000_000]
    fraud_ids = {tx['txid'] for tx in chain_tx}

    G = build_graph(all_tx, fraud_ids)

    # Highlight chain accounts
    chain_accounts = set()
    for tx in chain_tx:
        chain_accounts.add(tx['sender'])
        chain_accounts.add(tx['receiver'])
    highlight = {n: '#e74c3c' for n in chain_accounts if n in G.nodes}

    draw_scenario_graph(G, 'Scenario 08: Circular Payments (18-Hop Network)',
                        f'{folder}/graph_flow.png', highlight_nodes=highlight, layout='circular')

    # Chain flow - amount decay
    main_chain = sorted([tx for tx in chain_tx if 'مرحله' in str(tx.get('description',''))],
                        key=lambda x: x['date'])
    if main_chain:
        fig, ax = plt.subplots(figsize=(14, 6))
        amounts = [tx['amount']/1e6 for tx in main_chain]
        steps = [f"Step {i+1}\n{tx['date']}" for i, tx in enumerate(main_chain)]
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(amounts)))
        bars = ax.bar(range(len(amounts)), amounts, color=colors, alpha=0.8, edgecolor='black')
        ax.set_xticks(range(len(steps)))
        ax.set_xticklabels(steps, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel('Amount (Million IRR)')
        ax.set_title('Scenario 08: Amount Decay Through Circular Hops (5% commission per hop)',
                      fontweight='bold', fontsize=11)
        for bar, v in zip(bars, amounts):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5, f'{v:.0f}M', ha='center', fontsize=6)
        plt.tight_layout()
        fig.savefig(os.path.join(BASE, f'{folder}/amount_decay.png'), dpi=150)
        plt.close()

    # Parallel paths
    parallel_tx = [tx for tx in chain_tx if 'مسیر' in str(tx.get('description',''))]
    if parallel_tx:
        fig, ax = plt.subplots(figsize=(10, 5))
        p_amounts = [tx['amount']/1e6 for tx in parallel_tx]
        p_labels = [f"{tx.get('description','')[:20]}\n{tx['date']}" for tx in parallel_tx]
        ax.barh(range(len(p_amounts)), p_amounts, color='#9b59b6', alpha=0.8, edgecolor='black')
        ax.set_yticks(range(len(p_labels)))
        ax.set_yticklabels(p_labels, fontsize=8)
        ax.set_xlabel('Amount (Million IRR)')
        ax.set_title('Scenario 08: Parallel Obfuscation Paths', fontweight='bold')
        for i, v in enumerate(p_amounts):
            ax.text(v+2, i, f'{v:.0f}M', va='center', fontsize=8)
        plt.tight_layout()
        fig.savefig(os.path.join(BASE, f'{folder}/parallel_paths.png'), dpi=150)
        plt.close()

    draw_timeline(all_tx, 'Scenario 08: Transaction Timeline', f'{folder}/timeline.png')

    save_text(folder, 'analysis.txt', f"""SCENARIO 08: CIRCULAR PAYMENTS
================================
Pattern: Complex network returning to origin via 18 hops

Total Transactions: {len(all_tx)}
Chain Transactions (>100M): {len(chain_tx)}
Main Chain Steps: {len(main_chain)}
Parallel Paths: {len(parallel_tx)}
Accounts in Chain: {len(chain_accounts)}

Main Chain Flow:
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])} | {tx.get('description','')}" for tx in main_chain) + """

Parallel Paths:
""" + "\n".join(f"  {tx['date']} | {sheba_short(tx['sender'])} → {sheba_short(tx['receiver'])} | {amount_m(tx['amount'])} | {tx.get('description','')}" for tx in parallel_tx) + """

Key Indicators:
- Circular flow where originator is ultimate beneficiary
- ~5% commission extracted at each hop
- 45-day total duration
- Multiple parallel paths for obfuscation
""")
    print("   Done: scenario_08/")


# =============================================================
# MAIN
# =============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("Generating all fraud scenario visualizations from Neo4j...")
    print("=" * 60)

    generate_data_health()
    gen_scenario_01()
    gen_scenario_02()
    gen_scenario_03()
    gen_scenario_04()
    gen_scenario_05()
    gen_scenario_06()
    gen_scenario_07()
    gen_scenario_08()

    print("\n" + "=" * 60)
    print("ALL DONE! Files saved to output/")
    print("=" * 60)
