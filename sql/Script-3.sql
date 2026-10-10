SELECT COUNT(*) FROM bronze.transactions t
LEFT JOIN bronze.accounts a ON a.account_id = t.account_id
WHERE a.account_id IS NULL;