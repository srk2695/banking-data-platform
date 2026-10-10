SELECT transaction_id, COUNT(*) FROM bronze.transactions
GROUP BY transaction_id HAVING COUNT(*) > 1;