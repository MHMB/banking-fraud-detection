"""Detection query per scenario, as printed in the report.

`scenario` is only the dataset partition; no query reads the ground truth.
Every query returns paths (`p`) so the result can be drawn and scored.
"""

QUERIES = {
"01": """MATCH p = (d:Transaction {scenario:'scenario_01', type:'واریز نقدی'})-[:RECEIVED]->(a:Account)
          -[:SENT]->(t1:Transaction {scenario:'scenario_01'})-[:RECEIVED]->(b:Account)
          -[:SENT]->(t2:Transaction {scenario:'scenario_01'})-[:RECEIVED]->(c:Account)
          -[:SENT]->(t3:Transaction {scenario:'scenario_01'})-[:RECEIVED]->(e:Account)
WHERE d.date <= t1.date < t2.date < t3.date
  AND 0.95 * d.amount  <= t1.amount <= d.amount
  AND 0.95 * t1.amount <= t2.amount <= t1.amount
  AND 0.95 * t2.amount <= t3.amount <= t2.amount
RETURN p""",

"02": """MATCH p = (d:Transaction {scenario:'scenario_02', type:'واریز نقدی'})-[:RECEIVED]->(s:Account)
          -[:SENT]->(t:Transaction {scenario:'scenario_02'})-[:RECEIVED]->(agg:Account)
WHERE 40000000 <= d.amount < 50000000
  AND t.date = d.date AND 0.95 * d.amount <= t.amount <= d.amount
WITH agg, collect(p) AS paths, count(DISTINCT s) AS smurfs
WHERE smurfs >= 3
UNWIND paths AS p
RETURN p""",

"03": """MATCH p = (a:Account)-[:SENT]->(t1:Transaction {scenario:'scenario_03'})-[:RECEIVED]->(b:Account)
          -[:SENT]->(t2:Transaction {scenario:'scenario_03'})-[:RECEIVED]->(c:Account)
          -[:SENT]->(t3:Transaction {scenario:'scenario_03'})-[:RECEIVED]->(a)
WHERE a <> b AND b <> c AND a <> c
  AND t1.date < t2.date < t3.date
  AND 0.9 * t1.amount <= t2.amount <= t1.amount
  AND 0.9 * t2.amount <= t3.amount <= t2.amount
RETURN p""",

"04": """MATCH (donor:Account)-[:SENT]->(d:Transaction {scenario:'scenario_04'})-[:RECEIVED]->(hub:Account)
WHERE d.amount <= 5000000
WITH hub, count(DISTINCT donor) AS donors, sum(d.amount) AS collected
WHERE donors >= 20
MATCH p = (hub)-[:SENT]->(t1:Transaction {scenario:'scenario_04'})-[:RECEIVED]->(mid:Account)
          -[:SENT]->(t2:Transaction {scenario:'scenario_04'})-[:RECEIVED]->(dst:Account)
WHERE (dst)<-[:OWNS_ACCOUNT]-(:ForeignNational)
  AND t1.date <= t2.date
  AND t1.amount >= 0.2 * collected AND 0.8 * t1.amount <= t2.amount <= t1.amount
MATCH q = (:Account)-[:SENT]->(d2:Transaction {scenario:'scenario_04'})-[:RECEIVED]->(hub)
WHERE d2.amount <= 5000000
RETURN p, collect(q) AS donations""",

"05": """MATCH (a:Account)-[:SENT]->(t:Transaction {scenario:'scenario_05'})
WITH a, percentileCont(t.amount, 0.5) AS typical
MATCH p = (a)-[:SENT]->(x:Transaction {scenario:'scenario_05'})-[:RECEIVED]->(:Account)
WHERE x.amount >= 20 * typical AND x.time < '060000'
RETURN p""",

"06": """MATCH p = (imp:Account)-[:SENT]->(t1:Transaction {scenario:'scenario_06'})-[:RECEIVED]->(broker:Account)
          -[:SENT]->(t2:Transaction {scenario:'scenario_06'})-[:RECEIVED]->(exp:Account)
WHERE (exp)<-[:OWNS_ACCOUNT]-(:ForeignNational)
  AND t1.amount >= 500000000
  AND t1.date < t2.date
  AND 0.80 * t1.amount <= t2.amount <= 0.90 * t1.amount
RETURN p""",

"07": """MATCH p = (v:Account)-[:SENT]->(t:Transaction {scenario:'scenario_07', channel:'شعبه'})-[:RECEIVED]->(m:Account)
WHERE t.amount >= 50000000
  AND NOT EXISTS { (v)-[:SENT]->(o:Transaction {scenario:'scenario_07'}) WHERE o <> t }
  AND NOT EXISTS { (:Transaction {scenario:'scenario_07'})-[:RECEIVED]->(v) }
WITH v.bank_code AS bank, v.branch_code AS branch, collect(p) AS paths
WHERE size(paths) >= 3
UNWIND paths AS p
RETURN p""",

"08": """MATCH p = (a:Account)
          ((:Account)-[:SENT]->(t:Transaction {scenario:'scenario_08'} WHERE t.amount >= 300000000)-[:RECEIVED]->(:Account)){3,20}
          (a)
WHERE all(i IN range(0, size(t) - 2)
          WHERE t[i].date < t[i+1].date AND 0.9 * t[i].amount <= t[i+1].amount <= t[i].amount)
RETURN p""",

"09": """MATCH p = (s:Account)-[:SENT]->(t1:Transaction {scenario:'scenario_09'})-[:RECEIVED]->(m:Account)
          -[:SENT]->(t2:Transaction {scenario:'scenario_09'})-[:RECEIVED]->(g:Account)
WHERE s <> g AND t1.date < t2.date
  AND 0.8 * t1.amount <= t2.amount <= t1.amount
WITH s, g, collect(p) AS paths, count(DISTINCT m) AS branches
WHERE branches >= 3
UNWIND paths AS p
RETURN p""",
}
