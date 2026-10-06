// =====================================================
// Iranian Banking Fraud Detection - Import Script v5
// Neo4j 5.26.2 compatible, no plugins required
//
// Customer-type values in accounts_master.csv use Arabic
// yeh (ي, U+064A) as in real bank reports: 'حقيقي ايراني',
// 'حقيقي اتباع خارجي', 'حقوقي'. Literals below must match.
//
// Cash deposits have no sender_sheba and cash withdrawals
// no receiver_sheba, so those transactions get only one
// of SENT / RECEIVED.
//
// ground_truth.csv files are intentionally NOT imported:
// detection queries must find the fraud on their own.
// =====================================================


// ----------------------------------------------------
// STEP 1: Constraints and Indexes
// ----------------------------------------------------

CREATE CONSTRAINT sheba_unique    IF NOT EXISTS FOR (a:Account)     REQUIRE a.sheba          IS UNIQUE;
CREATE CONSTRAINT tx_unique       IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE;
CREATE CONSTRAINT shab_unique     IF NOT EXISTS FOR (c:Customer)    REQUIRE c.shab_id        IS UNIQUE;
CREATE CONSTRAINT bank_unique     IF NOT EXISTS FOR (b:Bank)        REQUIRE b.bank_code      IS UNIQUE;

CREATE INDEX tx_date_index        IF NOT EXISTS FOR (t:Transaction) ON (t.date);
CREATE INDEX tx_amount_index      IF NOT EXISTS FOR (t:Transaction) ON (t.amount);
CREATE INDEX tx_scenario_index    IF NOT EXISTS FOR (t:Transaction) ON (t.scenario);
CREATE INDEX account_status_index IF NOT EXISTS FOR (a:Account)     ON (a.status);


// ----------------------------------------------------
// STEP 2: Banks, Customers, Accounts (accounts_master.csv,
// one row per customer-account relationship)
// ----------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///accounts_master.csv' AS row
MERGE (bank:Bank {bank_code: row.`کد بانک`})
  SET bank.name = row.`نام بانک`
MERGE (c:Customer {shab_id: row.`شناسه شهاب`})
  SET c.customer_type = row.`نوع مشتری`
FOREACH (_ IN CASE WHEN row.`نوع مشتری` = 'حقوقي' THEN [1] ELSE [] END |
  SET c:Company, c.name = row.`نام خانوادگی`, c.national_id = row.`شناسه ملی`)
FOREACH (_ IN CASE WHEN row.`نوع مشتری` <> 'حقوقي' THEN [1] ELSE [] END |
  SET c:Person, c.first_name = row.`نام`, c.last_name = row.`نام خانوادگی`)
FOREACH (_ IN CASE WHEN row.`نوع مشتری` = 'حقيقي ايراني' THEN [1] ELSE [] END |
  SET c.national_id = row.`شماره ملی`)
FOREACH (_ IN CASE WHEN row.`نوع مشتری` = 'حقيقي اتباع خارجي' THEN [1] ELSE [] END |
  SET c:ForeignNational, c.fida_code = row.`شناسه اختصاصی اتباع خارجی`)
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
      account.in_master         = true
MERGE (account)-[:BELONGS_TO_BANK]->(bank)
MERGE (c)-[:OWNS_ACCOUNT {
  share:             toIntegerOrNull(row.`قدرالسهم`),
  has_withdrawal:    row.`حق برداشت`,
  relationship_type: row.`نوع ارتباط با حساب`
}]->(account)
// Account-level customer type = primary owner's type
FOREACH (_ IN CASE WHEN row.`کد نوع ارتباط با حساب` = '1' THEN [1] ELSE [] END |
  SET account.customer_type = row.`نوع مشتری`);


// ----------------------------------------------------
// STEP 3: Transactions - all scenarios.
// A Sheba missing from the master file still gets an
// Account node (in_master = false) so no tx is dropped.
// ----------------------------------------------------

UNWIND ['01', '02', '03', '04', '05', '06', '07', '08', '09'] AS n
CALL {
  WITH n
  LOAD CSV WITH HEADERS FROM 'file:///scenario_' + n + '/transactions.csv' AS row
  MERGE (tx:Transaction {transaction_id: row.transaction_id})
    SET tx.date           = row.date,
        tx.time           = row.time,
        tx.amount         = toIntegerOrNull(row.amount),
        tx.currency       = row.currency,
        tx.type           = row.type,
        tx.description    = row.description,
        tx.reference      = row.reference,
        tx.channel        = row.channel,
        tx.status         = row.status,
        tx.scenario       = 'scenario_' + n,
        tx.sender_sheba   = row.sender_sheba,
        tx.receiver_sheba = row.receiver_sheba
  FOREACH (sheba IN CASE WHEN row.sender_sheba IS NULL THEN [] ELSE [row.sender_sheba] END |
    MERGE (s:Account {sheba: sheba}) ON CREATE SET s.in_master = false
    MERGE (s)-[:SENT]->(tx))
  FOREACH (sheba IN CASE WHEN row.receiver_sheba IS NULL THEN [] ELSE [row.receiver_sheba] END |
    MERGE (r:Account {sheba: sheba}) ON CREATE SET r.in_master = false
    MERGE (tx)-[:RECEIVED]->(r))
} IN TRANSACTIONS OF 500 ROWS;


// ----------------------------------------------------
// STEP 4: Verification
// ----------------------------------------------------

MATCH (n)
RETURN labels(n) AS Labels, count(n) AS Count
ORDER BY Count DESC;

MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC;

// Every transaction must have at least one side
MATCH (tx:Transaction)
WHERE NOT (tx)<-[:SENT]-() AND NOT (tx)-[:RECEIVED]->()
RETURN count(tx) AS orphaned_transactions;
