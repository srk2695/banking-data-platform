"""Bronze -> Silver with PySpark.

Reads data/bronze/*.csv, cleans it, writes Parquet to data/silver/.
Run from the project root:  python src/bronze_to_silver.py
"""
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parent.parent
BRONZE = ROOT / "data" / "bronze"
SILVER = ROOT / "data" / "silver"


def main():
    spark = SparkSession.builder.appName("bronze_to_silver").getOrCreate()

    def read(name):
        return spark.read.csv(str(BRONZE / f"{name}.csv"), header=True, inferSchema=True)

    customers, accounts, transactions = read("customers"), read("accounts"), read("transactions")

    silver_customers = (
        customers.dropDuplicates(["customer_id"])
        .select(
            "customer_id",
            F.initcap(F.trim("first_name")).alias("first_name"),
            F.initcap(F.trim("last_name")).alias("last_name"),
            F.lower(F.trim("email")).alias("email"),
            "phone",
            F.to_date("date_of_birth").alias("date_of_birth"),
            "city", "country", "segment",
            F.to_date("created_at").alias("created_at"),
        )
    )

    silver_accounts = accounts.select(
        "account_id", "customer_id", "account_type", "currency",
        F.to_date("opened_date").alias("opened_date"),
        F.upper(F.trim("status")).alias("status"),
        F.abs(F.col("balance").cast("double")).alias("balance"),
        (F.col("balance").cast("double") < 0).alias("balance_was_negative"),
    )

    acc_ids = silver_accounts.select("account_id").withColumn("acct_found", F.lit(True))
    joined = transactions.dropDuplicates(["transaction_id"]).join(acc_ids, "account_id", "left")

    silver_transactions = (
        joined.filter(F.col("acct_found").isNotNull() & F.col("amount").isNotNull())
        .select(
            "transaction_id", "account_id",
            F.col("txn_timestamp").cast("timestamp").alias("txn_timestamp"),
            F.upper(F.trim("txn_type")).alias("txn_type"),
            F.abs(F.col("amount").cast("double")).alias("amount"),
            (F.col("amount").cast("double") < 0).alias("amount_was_negative"),
            "currency", "merchant_category", "channel",
            F.upper(F.trim("status")).alias("status"),
        )
    )

    silver_rejected = (
        joined.filter(F.col("amount").isNull() | F.col("acct_found").isNull())
        .withColumn("reject_reason",
                    F.when(F.col("amount").isNull(), "NULL_AMOUNT").otherwise("ORPHAN_ACCOUNT"))
        .drop("acct_found")
    )

    outputs = {
        "customers": silver_customers,
        "accounts": silver_accounts,
        "transactions": silver_transactions,
        "transactions_rejected": silver_rejected,
    }
    for name, df in outputs.items():
        df.write.mode("overwrite").parquet(str(SILVER / name))
        print(f"{name:25s}{df.count():>8,} rows")

    spark.stop()


if __name__ == "__main__":
    main()