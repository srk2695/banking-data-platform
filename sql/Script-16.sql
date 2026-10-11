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