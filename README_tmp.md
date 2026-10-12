\# Banking Data Platform



End-to-end data engineering project using a medallion architecture (bronze, silver, gold) on PostgreSQL.



\## Architecture

\- \*\*Bronze:\*\* raw synthetic banking data (customers, accounts, transactions) with deliberate quality issues

\- \*\*Silver:\*\* cleaned data (deduplicated, standardised, invalid rows quarantined in `transactions\_rejected`)

\- \*\*Gold:\*\* star schema (`dim\_customer`, `dim\_account`, `fact\_transactions`) plus reporting tables



\## Star schema

!\[Star schema](docs/star\_schema.png)



`daily\_txn\_summary` and `customer\_summary` are reporting tables aggregated from `fact\_transactions`.



\## Stack

Python (Faker, pandas), PostgreSQL, DBeaver, Git. Planned: PySpark, Airflow, Power BI.



\## Project structure

\- `src/generate\_data.py`: generates the bronze CSVs

\- `sql/`: numbered scripts for quality checks, silver and gold layers

\- `docs/`: diagrams and notes



\## How to run

1\. `pip install faker pandas numpy`

2\. `python src/generate\_data.py`

3\. Load the CSVs from `data/bronze` into PostgreSQL schema `bronze`

4\. Run `sql/03\_silver\_layer.sql`, then `sql/04\_gold\_layer.sql`



\## Data quality rules (silver)

\- Duplicate IDs removed

\- Names, emails and statuses standardised

\- Negative amounts flagged and made positive

\- Null amounts and orphan account IDs moved to `silver.transactions\_rejected`

