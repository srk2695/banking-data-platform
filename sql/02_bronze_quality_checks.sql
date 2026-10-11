-- duplicate transaction IDs
SELECT transaction_id, COUNT(*) FROM bronze.transactions
GROUP BY transaction_id HAVING COUNT(*) > 1;

-- null or negative amounts
SELECT COUNT(*) FILTER (WHERE amount IS NULL) AS null_amounts,
       COUNT(*) FILTER (WHERE amount < 0) AS negative_amounts
FROM bronze.transactions;

-- transactions pointing to accounts that don't exist
SELECT COUNT(*) FROM bronze.transactions t
LEFT JOIN bronze.accounts a ON a.account_id = t.account_id
WHERE a.account_id IS NULL;