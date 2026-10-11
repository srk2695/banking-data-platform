CREATE SCHEMA IF NOT EXISTS gold;

DROP TABLE IF EXISTS gold.dim_customer;
CREATE TABLE gold.dim_customer AS
SELECT ROW_NUMBER() OVER (ORDER BY customer_id)   AS customer_key,
       customer_id,
       first_name || ' ' || last_name             AS full_name,
       email,
       city,
       country,
       segment,
       created_at,
       DATE_PART('year', AGE(CURRENT_DATE, date_of_birth))::int AS age
FROM silver.customers;

DROP TABLE IF EXISTS gold.dim_account;
CREATE TABLE gold.dim_account AS
SELECT ROW_NUMBER() OVER (ORDER BY a.account_id)  AS account_key,
       a.account_id,
       c.customer_key,
       a.account_type,
       a.currency,
       a.opened_date,
       a.status,
       a.balance
FROM silver.accounts a
JOIN gold.dim_customer c ON c.customer_id = a.customer_id;

DROP TABLE IF EXISTS gold.fact_transactions;
CREATE TABLE gold.fact_transactions AS
SELECT ROW_NUMBER() OVER (ORDER BY t.txn_timestamp, t.transaction_id) AS txn_key,
       t.transaction_id,
       a.account_key,
       a.customer_key,
       t.txn_timestamp,
       t.txn_timestamp::date   AS txn_date,
       t.txn_type,
       t.amount,
       t.amount_was_negative,
       t.currency,
       t.merchant_category,
       t.channel,
       t.status
FROM silver.transactions t
JOIN gold.dim_account a ON a.account_id = t.account_id;

DROP TABLE IF EXISTS gold.daily_txn_summary;
CREATE TABLE gold.daily_txn_summary AS
SELECT txn_date,
       currency,
       COUNT(*)                                        AS txn_count,
       COUNT(*) FILTER (WHERE status = 'COMPLETED')    AS completed_count,
       COUNT(*) FILTER (WHERE status = 'FAILED')       AS failed_count,
       ROUND(SUM(amount) FILTER (WHERE status = 'COMPLETED'), 2) AS completed_amount,
       ROUND(AVG(amount), 2)                           AS avg_amount
FROM gold.fact_transactions
GROUP BY txn_date, currency;

DROP TABLE IF EXISTS gold.customer_summary;
CREATE TABLE gold.customer_summary AS
WITH acc AS (
    SELECT customer_key, COUNT(*) AS account_count
    FROM gold.dim_account
    GROUP BY customer_key
),
txn AS (
    SELECT customer_key,
           COUNT(*)                                       AS txn_count,
           COUNT(*) FILTER (WHERE status = 'FAILED')      AS failed_count,
           MAX(txn_date)                                  AS last_txn_date,
           ROUND(SUM(amount) FILTER (WHERE status = 'COMPLETED' AND currency = 'AED'), 2) AS aed_amount,
           ROUND(SUM(amount) FILTER (WHERE status = 'COMPLETED' AND currency = 'USD'), 2) AS usd_amount,
           ROUND(SUM(amount) FILTER (WHERE status = 'COMPLETED' AND currency = 'EUR'), 2) AS eur_amount
    FROM gold.fact_transactions
    GROUP BY customer_key
)
SELECT c.customer_key,
       c.customer_id,
       c.full_name,
       c.segment,
       c.country,
       COALESCE(acc.account_count, 0)  AS account_count,
       COALESCE(txn.txn_count, 0)      AS txn_count,
       COALESCE(txn.failed_count, 0)   AS failed_count,
       txn.last_txn_date,
       COALESCE(txn.aed_amount, 0)     AS aed_amount,
       COALESCE(txn.usd_amount, 0)     AS usd_amount,
       COALESCE(txn.eur_amount, 0)     AS eur_amount
FROM gold.dim_customer c
LEFT JOIN acc ON acc.customer_key = c.customer_key
LEFT JOIN txn ON txn.customer_key = c.customer_key;