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