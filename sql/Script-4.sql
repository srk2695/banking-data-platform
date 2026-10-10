SELECT COUNT(*) FILTER (WHERE amount IS NULL) AS null_amounts,
       COUNT(*) FILTER (WHERE amount < 0) AS negative_amounts
FROM bronze.transactions;