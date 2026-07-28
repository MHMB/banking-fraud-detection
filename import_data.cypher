// =====================================================
// Iranian Banking Fraud Detection - Import Script v4
// Neo4j 5.26.2 compatible, no plugins required
// 
// Key fix in this version:
// Before loading transactions, we do a "sheba reconciliation"
// pass that creates placeholder Account nodes for any sheba
// that appears in a transaction file but is missing from
// accounts_master.csv. This ensures no transaction is
// silently dropped due to a missing account.
// =====================================================


// ----------------------------------------------------
// STEP 1: Constraints and Indexes
// ----------------------------------------------------

CREATE CONSTRAINT sheba_unique    IF NOT EXISTS FOR (a:Account)    REQUIRE a.sheba          IS UNIQUE;
CREATE CONSTRAINT tx_unique       IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE;
CREATE CONSTRAINT shab_unique     IF NOT EXISTS FOR (c:Customer)   REQUIRE c.shab_id        IS UNIQUE;
CREATE CONSTRAINT bank_unique     IF NOT EXISTS FOR (b:Bank)       REQUIRE b.bank_code      IS UNIQUE;

CREATE INDEX tx_date_index        IF NOT EXISTS FOR (t:Transaction) ON (t.date);
CREATE INDEX tx_amount_index      IF NOT EXISTS FOR (t:Transaction) ON (t.amount);
CREATE INDEX tx_scenario_index    IF NOT EXISTS FOR (t:Transaction) ON (t.scenario);
CREATE INDEX account_status_index IF NOT EXISTS FOR (a:Account)    ON (a.status);


// ----------------------------------------------------
// STEP 2: Bank Nodes
// ----------------------------------------------------

MERGE (:Bank {bank_code: '056', name: 'بانک سامان'});
MERGE (:Bank {bank_code: '058', name: 'بانک ملت'});
MERGE (:Bank {bank_code: '054', name: 'بانک پاسارگاد'});
MERGE (:Bank {bank_code: '051', name: 'بانک ملی'});
MERGE (:Bank {bank_code: '018', name: 'بانک تجارت'});
MERGE (:Bank {bank_code: '020', name: 'بانک سپه'});
MERGE (:Bank {bank_code: '021', name: 'بانک صادرات'});
MERGE (:Bank {bank_code: '015', name: 'بانک کشاورزی'});
MERGE (:Bank {bank_code: '019', name: 'بانک سینا'});
MERGE (:Bank {bank_code: '052', name: 'بانک شهر'});


// ----------------------------------------------------
// STEP 3: Customer Nodes (from accounts_master.csv)
// Three passes — one per customer type — avoids APOC.
// ----------------------------------------------------

// Iranian individuals
CALL {
  LOAD CSV WITH HEADERS FROM 'file:///accounts_master.csv' AS row
  WITH row WHERE row.`شناسه شهاب` IS NOT NULL
    AND row.`نوع مشتری` <> 'حقوقی'
    AND row.`نوع مشتری` <> 'حقیقی اتباع خارجی'
  MERGE (c:Customer:Person {shab_id: row.`شناسه شهاب`})
    SET c.first_name    = row.`نام`,
        c.last_name     = row.`نام خانوادگی`,
        c.national_id   = row.`شماره ملی`,
        c.customer_type = row.`نوع مشتری`
} IN TRANSACTIONS OF 500 ROWS;

// Foreign nationals
CALL {
  LOAD CSV WITH HEADERS FROM 'file:///accounts_master.csv' AS row
  WITH row WHERE row.`شناسه شهاب` IS NOT NULL
    AND row.`نوع مشتری` = 'حقیقی اتباع خارجی'
  MERGE (c:Customer:Person:ForeignNational {shab_id: row.`شناسه شهاب`})
    SET c.first_name    = row.`نام`,
        c.last_name     = row.`نام خانوادگی`,
        c.fida_code     = row.`شناسه اختصاصی اتباع خارجی`,
        c.customer_type = row.`نوع مشتری`
} IN TRANSACTIONS OF 500 ROWS;

// Legal entities / companies
CALL {
  LOAD CSV WITH HEADERS FROM 'file:///accounts_master.csv' AS row
  WITH row WHERE row.`شناسه شهاب` IS NOT NULL
    AND row.`نوع مشتری` = 'حقوقی'
  MERGE (c:Customer:Company {shab_id: row.`شناسه شهاب`})
    SET c.name          = row.`نام` + ' ' + row.`نام خانوادگی`,
        c.customer_type = row.`نوع مشتری`
} IN TRANSACTIONS OF 500 ROWS;


// ----------------------------------------------------
// STEP 4: Account Nodes + Relationships (from master)
// ----------------------------------------------------

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///accounts_master.csv' AS row
  WITH row WHERE row.`شماره شبای حساب` IS NOT NULL
  MATCH (bank:Bank         {bank_code: row.`کد بانک`})
  MATCH (customer:Customer {shab_id:   row.`شناسه شهاب`})
  MERGE (account:Account {sheba: row.`شماره شبای حساب`})
    SET account.bank_code         = row.`کد بانک`,
        account.bank_name         = row.`نام بانک`,
        account.branch_code       = row.`کد شعبه افتتاح کننده`,
        account.account_type_code = row.`کد نوع حساب`,
        account.account_type      = row.`نوع حساب`,
        account.currency_code     = row.`کد ارز`,
        account.currency_name     = row.`نوع ارز`,
        account.opening_date      = row.`تاریخ افتتاح حساب`,
        account.status_code       = row.`کد وضعیت حساب`,
        account.status            = row.`وضعیت حساب`,
        account.customer_type     = row.`نوع مشتری`,
        account.in_master         = true
  MERGE (account)-[:BELONGS_TO_BANK]->(bank)
  MERGE (customer)-[:OWNS_ACCOUNT {
    share:             toIntegerOrNull(row.`قدرالسهم`),
    has_withdrawal:    row.`حق برداشت`,
    relationship_type: row.`نوع ارتباط با حساب`
  }]->(account)
} IN TRANSACTIONS OF 500 ROWS;


// ----------------------------------------------------
// STEP 5: Sheba Reconciliation — create placeholder
// Account nodes for any sheba that appears in a
// transaction file but is missing from accounts_master.
//
// WHY THIS MATTERS: The scenario CSV files contain sheba
// numbers for accounts that were not included in the
// master file (they may belong to external banks, or are
// deliberately omitted to simulate partial data). Without
// this step, any transaction referencing a missing sheba
// is silently dropped — the transaction node is created
// but no relationships are formed, leaving orphaned nodes.
//
// We mark these with in_master=false so you can always
// distinguish "known" accounts from "placeholder" ones.
// We run one pass per scenario file (UNION not allowed
// inside CALL...IN TRANSACTIONS in Neo4j 5).
// ----------------------------------------------------

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_01/transactions.csv' AS row
  WITH row WHERE row.sender_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.sender_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_01/transactions.csv' AS row
  WITH row WHERE row.receiver_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.receiver_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_02/transactions.csv' AS row
  WITH row WHERE row.sender_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.sender_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_02/transactions.csv' AS row
  WITH row WHERE row.receiver_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.receiver_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_03/transactions.csv' AS row
  WITH row WHERE row.sender_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.sender_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_03/transactions.csv' AS row
  WITH row WHERE row.receiver_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.receiver_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_04/transactions.csv' AS row
  WITH row WHERE row.sender_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.sender_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_04/transactions.csv' AS row
  WITH row WHERE row.receiver_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.receiver_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_05/transactions.csv' AS row
  WITH row WHERE row.sender_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.sender_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_05/transactions.csv' AS row
  WITH row WHERE row.receiver_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.receiver_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_06/transactions.csv' AS row
  WITH row WHERE row.sender_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.sender_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_06/transactions.csv' AS row
  WITH row WHERE row.receiver_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.receiver_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_07/transactions.csv' AS row
  WITH row WHERE row.sender_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.sender_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_07/transactions.csv' AS row
  WITH row WHERE row.receiver_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.receiver_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_08/transactions.csv' AS row
  WITH row WHERE row.sender_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.sender_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_08/transactions.csv' AS row
  WITH row WHERE row.receiver_sheba IS NOT NULL
  MERGE (a:Account {sheba: row.receiver_sheba})
    ON CREATE SET a.in_master = false
} IN TRANSACTIONS OF 500 ROWS;


// ----------------------------------------------------
// STEP 6: Transaction Nodes — all 8 scenarios
//
// Two important changes vs. previous versions:
// 1. We now use MATCH (guaranteed to find the Account
//    node because Step 5 created placeholders for all
//    shebas), so no transactions are silently skipped.
// 2. We store sender_sheba and receiver_sheba as
//    properties on the Transaction node itself, so you
//    can query them directly without traversing edges.
//    Both approaches (property lookup and relationship
//    traversal) will work correctly.
// ----------------------------------------------------

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_01/transactions.csv' AS row
  WITH row WHERE row.transaction_id IS NOT NULL
  MATCH (s:Account {sheba: row.sender_sheba})
  MATCH (r:Account {sheba: row.receiver_sheba})
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date          = row.date,
        tx.time          = row.time,
        tx.amount        = toIntegerOrNull(row.amount),
        tx.currency      = row.currency,
        tx.type          = row.type,
        tx.description   = row.description,
        tx.reference     = row.reference,
        tx.channel       = row.channel,
        tx.status        = row.status,
        tx.scenario      = 'scenario_01',
        tx.sender_sheba  = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  MERGE (s)-[:SENT]->(tx)
  MERGE (tx)-[:RECEIVED]->(r)
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_02/transactions.csv' AS row
  WITH row WHERE row.transaction_id IS NOT NULL
  MATCH (s:Account {sheba: row.sender_sheba})
  MATCH (r:Account {sheba: row.receiver_sheba})
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date          = row.date,
        tx.time          = row.time,
        tx.amount        = toIntegerOrNull(row.amount),
        tx.currency      = row.currency,
        tx.type          = row.type,
        tx.description   = row.description,
        tx.reference     = row.reference,
        tx.channel       = row.channel,
        tx.status        = row.status,
        tx.scenario      = 'scenario_02',
        tx.sender_sheba  = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  MERGE (s)-[:SENT]->(tx)
  MERGE (tx)-[:RECEIVED]->(r)
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_03/transactions.csv' AS row
  WITH row WHERE row.transaction_id IS NOT NULL
  MATCH (s:Account {sheba: row.sender_sheba})
  MATCH (r:Account {sheba: row.receiver_sheba})
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date          = row.date,
        tx.time          = row.time,
        tx.amount        = toIntegerOrNull(row.amount),
        tx.currency      = row.currency,
        tx.type          = row.type,
        tx.description   = row.description,
        tx.reference     = row.reference,
        tx.channel       = row.channel,
        tx.status        = row.status,
        tx.scenario      = 'scenario_03',
        tx.sender_sheba  = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  MERGE (s)-[:SENT]->(tx)
  MERGE (tx)-[:RECEIVED]->(r)
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_04/transactions.csv' AS row
  WITH row WHERE row.transaction_id IS NOT NULL
  MATCH (s:Account {sheba: row.sender_sheba})
  MATCH (r:Account {sheba: row.receiver_sheba})
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date          = row.date,
        tx.time          = row.time,
        tx.amount        = toIntegerOrNull(row.amount),
        tx.currency      = row.currency,
        tx.type          = row.type,
        tx.description   = row.description,
        tx.reference     = row.reference,
        tx.channel       = row.channel,
        tx.status        = row.status,
        tx.scenario      = 'scenario_04',
        tx.sender_sheba  = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  MERGE (s)-[:SENT]->(tx)
  MERGE (tx)-[:RECEIVED]->(r)
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_05/transactions.csv' AS row
  WITH row WHERE row.transaction_id IS NOT NULL
  MATCH (s:Account {sheba: row.sender_sheba})
  MATCH (r:Account {sheba: row.receiver_sheba})
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date          = row.date,
        tx.time          = row.time,
        tx.amount        = toIntegerOrNull(row.amount),
        tx.currency      = row.currency,
        tx.type          = row.type,
        tx.description   = row.description,
        tx.reference     = row.reference,
        tx.channel       = row.channel,
        tx.status        = row.status,
        tx.scenario      = 'scenario_05',
        tx.sender_sheba  = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  MERGE (s)-[:SENT]->(tx)
  MERGE (tx)-[:RECEIVED]->(r)
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_06/transactions.csv' AS row
  WITH row WHERE row.transaction_id IS NOT NULL
  MATCH (s:Account {sheba: row.sender_sheba})
  MATCH (r:Account {sheba: row.receiver_sheba})
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date          = row.date,
        tx.time          = row.time,
        tx.amount        = toIntegerOrNull(row.amount),
        tx.currency      = row.currency,
        tx.type          = row.type,
        tx.description   = row.description,
        tx.reference     = row.reference,
        tx.channel       = row.channel,
        tx.status        = row.status,
        tx.scenario      = 'scenario_06',
        tx.sender_sheba  = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  MERGE (s)-[:SENT]->(tx)
  MERGE (tx)-[:RECEIVED]->(r)
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_07/transactions.csv' AS row
  WITH row WHERE row.transaction_id IS NOT NULL
  MATCH (s:Account {sheba: row.sender_sheba})
  MATCH (r:Account {sheba: row.receiver_sheba})
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date          = row.date,
        tx.time          = row.time,
        tx.amount        = toIntegerOrNull(row.amount),
        tx.currency      = row.currency,
        tx.type          = row.type,
        tx.description   = row.description,
        tx.reference     = row.reference,
        tx.channel       = row.channel,
        tx.status        = row.status,
        tx.scenario      = 'scenario_07',
        tx.sender_sheba  = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  MERGE (s)-[:SENT]->(tx)
  MERGE (tx)-[:RECEIVED]->(r)
} IN TRANSACTIONS OF 500 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///scenario_08/transactions.csv' AS row
  WITH row WHERE row.transaction_id IS NOT NULL
  MATCH (s:Account {sheba: row.sender_sheba})
  MATCH (r:Account {sheba: row.receiver_sheba})
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date          = row.date,
        tx.time          = row.time,
        tx.amount        = toIntegerOrNull(row.amount),
        tx.currency      = row.currency,
        tx.type          = row.type,
        tx.description   = row.description,
        tx.reference     = row.reference,
        tx.channel       = row.channel,
        tx.status        = row.status,
        tx.scenario      = 'scenario_08',
        tx.sender_sheba  = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  MERGE (s)-[:SENT]->(tx)
  MERGE (tx)-[:RECEIVED]->(r)
} IN TRANSACTIONS OF 500 ROWS;


// ----------------------------------------------------
// STEP 7: Verification
// ----------------------------------------------------

MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Count
ORDER BY Count DESC;

MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC;

// Sanity check: any orphaned transaction nodes left?
// (transactions with no SENT or RECEIVED relationships)
MATCH (tx:Transaction)
WHERE NOT (tx)<-[:SENT]-() OR NOT (tx)-[:RECEIVED]->()
RETURN count(tx) AS orphaned_transactions;
