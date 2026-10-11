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