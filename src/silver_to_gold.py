"""Silver -> Gold with PySpark.

Reads data/silver (Parquet), builds the star schema and reporting tables,
writes Parquet to data/gold/.
Run from the project root:  python src/silver_to_gold.py
"""
from pathlib import Path

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parent.parent
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"


def main():
    spark = SparkSession.builder.appName("silver_to_gold").getOrCreate()

    def read(name):
        return spark.read.parquet(str(SILVER / name))

    customers, accounts, transactions = read("customers"), read("accounts"), read("transactions")

    dim_customer = (
        customers
        .withColumn("customer_key", F.row_number().over(Window.orderBy("customer_id")))
        .select(
            "customer_key", "customer_id",
            F.concat_ws(" ", "first_name", "last_name").alias("full_name"),
            "email", "city", "country", "segment", "created_at",
            F.floor(F.months_between(F.current_date(), "date_of_birth") / 12).cast("int").alias("age"),
        )
    )

    dim_account = (
        accounts
        .join(dim_customer.select("customer_key", "customer_id"), "customer_id")
        .withColumn("account_key", F.row_number().over(Window.orderBy("account_id")))
        .select("account_key", "account_id", "customer_key", "account_type",
                "currency", "opened_date", "status", "balance")
    )

    fact_transactions = (
        transactions
        .join(dim_account.select("account_id", "account_key", "customer_key"), "account_id")
        .withColumn("txn_date", F.to_date("txn_timestamp"))
        .withColumn("txn_key", F.row_number().over(Window.orderBy("txn_timestamp", "transaction_id")))
        .select("txn_key", "transaction_id", "account_key", "customer_key",
                "txn_timestamp", "txn_date", "txn_type", "amount",
                "amount_was_negative", "currency", "merchant_category",
                "channel", "status")
    )

    daily_txn_summary = (
        fact_transactions.groupBy("txn_date", "currency")
        .agg(
            F.count("*").alias("txn_count"),
            F.sum(F.when(F.col("status") == "COMPLETED", 1).otherwise(0)).alias("completed_count"),
            F.sum(F.when(F.col("status") == "FAILED", 1).otherwise(0)).alias("failed_count"),
            F.round(F.sum(F.when(F.col("status") == "COMPLETED", F.col("amount"))), 2).alias("completed_amount"),
            F.round(F.avg("amount"), 2).alias("avg_amount"),
        )
    )

    def completed_in(cur):
        return F.round(F.sum(F.when((F.col("status") == "COMPLETED") & (F.col("currency") == cur),
                                    F.col("amount"))), 2)

    txn_agg = (
        fact_transactions.groupBy("customer_key")
        .agg(
            F.count("*").alias("txn_count"),
            F.sum(F.when(F.col("status") == "FAILED", 1).otherwise(0)).alias("failed_count"),
            F.max("txn_date").alias("last_txn_date"),
            completed_in("AED").alias("aed_amount"),
            completed_in("USD").alias("usd_amount"),
            completed_in("EUR").alias("eur_amount"),
        )
    )
    acc_agg = dim_account.groupBy("customer_key").agg(F.count("*").alias("account_count"))

    customer_summary = (
        dim_customer.select("customer_key", "customer_id", "full_name", "segment", "country")
        .join(acc_agg, "customer_key", "left")
        .join(txn_agg, "customer_key", "left")
        .fillna(0, subset=["account_count", "txn_count", "failed_count",
                           "aed_amount", "usd_amount", "eur_amount"])
    )

    outputs = {
        "dim_customer": dim_customer,
        "dim_account": dim_account,
        "fact_transactions": fact_transactions,
        "daily_txn_summary": daily_txn_summary,
        "customer_summary": customer_summary,
    }
    for name, df in outputs.items():
        df.write.mode("overwrite").parquet(str(GOLD / name))
        print(f"{name:20s}{df.count():>8,} rows")

    spark.stop()


if __name__ == "__main__":
    main()