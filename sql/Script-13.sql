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