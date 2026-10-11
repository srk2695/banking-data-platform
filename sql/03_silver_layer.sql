CREATE SCHEMA IF NOT EXISTS silver;

DROP TABLE IF EXISTS silver.customers;
CREATE TABLE silver.customers AS
SELECT DISTINCT ON (customer_id)
       customer_id,
       INITCAP(TRIM(first_name))  AS first_name,
       INITCAP(TRIM(last_name))   AS last_name,
       LOWER(TRIM(email))         AS email,
       phone,
       date_of_birth::date        AS date_of_birth,
       city,
       country,
       segment,
       created_at::date           AS created_at
FROM bronze.customers
ORDER BY customer_id;

DROP TABLE IF EXISTS silver.accounts;
CREATE TABLE silver.accounts AS
SELECT account_id,
       customer_id,
       account_type,
       currency,
       opened_date::date               AS opened_date,
       UPPER(TRIM(status))             AS status,
       ABS(balance::numeric)           AS balance,
       (balance::numeric < 0)          AS balance_was_negative
FROM bronze.accounts;

DROP TABLE IF EXISTS silver.transactions;
CREATE TABLE silver.transactions AS
WITH dedup AS (
    SELECT DISTINCT ON (transaction_id) *
    FROM bronze.transactions
    ORDER BY transaction_id
)
SELECT t.transaction_id,
       t.account_id,
       t.txn_timestamp::timestamp      AS txn_timestamp,
       UPPER(TRIM(t.txn_type))         AS txn_type,
       ABS(t.amount::numeric)          AS amount,
       (t.amount::numeric < 0)         AS amount_was_negative,
       t.currency,
       t.merchant_category,
       t.channel,
       UPPER(TRIM(t.status))           AS status
FROM dedup t
JOIN silver.accounts a ON a.account_id = t.account_id
WHERE t.amount IS NOT NULL;

DROP TABLE IF EXISTS silver.transactions_rejected;
CREATE TABLE silver.transactions_rejected AS
WITH dedup AS (
    SELECT DISTINCT ON (transaction_id) *
    FROM bronze.transactions
    ORDER BY transaction_id
)
SELECT t.*,
       CASE WHEN t.amount IS NULL THEN 'NULL_AMOUNT'
            ELSE 'ORPHAN_ACCOUNT' END AS reject_reason
FROM dedup t
LEFT JOIN silver.accounts a ON a.account_id = t.account_id
WHERE t.amount IS NULL OR a.account_id IS NULL;