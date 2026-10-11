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