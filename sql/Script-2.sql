SELECT 'customers' AS tbl, COUNT(*) FROM bronze.customers
UNION ALL SELECT 'accounts', COUNT(*) FROM bronze.accounts
UNION ALL SELECT 'transactions', COUNT(*) FROM bronze.transactions;