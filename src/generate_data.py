"""Generate synthetic banking data (bronze layer).

Writes customers.csv, accounts.csv and transactions.csv to <project>/data/bronze.

Usage (from the project root, venv active):
    python src\generate_data.py
    python src\generate_data.py --customers 5000 --transactions 100000
    python src\generate_data.py --clean      # no deliberate data-quality issues
"""
import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "bronze"

SEGMENTS = ["RETAIL", "PREMIUM", "SME", "PRIVATE"]
ACCOUNT_TYPES = ["SAVINGS", "CHECKING", "CREDIT_CARD", "LOAN"]
CURRENCIES = ["AED", "USD", "EUR"]
TXN_TYPES = ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT", "FEE"]
CHANNELS = ["ATM", "MOBILE", "ONLINE", "BRANCH", "POS"]
MERCHANT_CATEGORIES = [
    "GROCERY", "TRAVEL", "DINING", "UTILITIES", "SHOPPING",
    "HEALTHCARE", "ENTERTAINMENT", "FUEL", "OTHER",
]
STATUSES = ["COMPLETED", "PENDING", "FAILED", "REVERSED"]


def make_customers(fake, rng, n):
    today = date.today()
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "customer_id": f"C{i:06d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat(),
            "city": fake.city(),
            "country": fake.country_code(),
            "segment": rng.choice(SEGMENTS, p=[0.65, 0.2, 0.12, 0.03]),
            "created_at": fake.date_between(today - timedelta(days=8 * 365), today - timedelta(days=1)).isoformat(),
        })
    return pd.DataFrame(rows)


def make_accounts(rng, customers):
    today = date.today()
    rows = []
    acc_no = 1
    for cust_id, created in zip(customers["customer_id"], customers["created_at"]):
        created_d = date.fromisoformat(created)
        max_offset = max((today - created_d).days, 1)
        for _ in range(int(rng.integers(1, 4))):  # 1-3 accounts per customer
            opened = created_d + timedelta(days=int(rng.integers(0, max_offset)))
            rows.append({
                "account_id": f"A{acc_no:07d}",
                "customer_id": cust_id,
                "account_type": rng.choice(ACCOUNT_TYPES, p=[0.4, 0.35, 0.15, 0.1]),
                "currency": rng.choice(CURRENCIES, p=[0.7, 0.2, 0.1]),
                "opened_date": opened.isoformat(),
                "status": rng.choice(["ACTIVE", "DORMANT", "CLOSED"], p=[0.85, 0.1, 0.05]),
                "balance": round(float(rng.lognormal(mean=8.5, sigma=1.2)), 2),
            })
            acc_no += 1
    return pd.DataFrame(rows)


def make_transactions(rng, accounts, n):
    acc_idx = rng.integers(0, len(accounts), size=n)
    acc_ids = accounts["account_id"].to_numpy()[acc_idx]
    currencies = accounts["currency"].to_numpy()[acc_idx]

    end = pd.Timestamp.now().floor("s")
    start = end - pd.Timedelta(days=365)
    seconds = rng.integers(0, int((end - start).total_seconds()), size=n)
    timestamps = start + pd.to_timedelta(seconds, unit="s")

    txn_types = rng.choice(TXN_TYPES, size=n, p=[0.2, 0.2, 0.2, 0.35, 0.05])
    amounts = np.round(rng.lognormal(mean=4.5, sigma=1.1, size=n), 2)

    df = pd.DataFrame({
        "transaction_id": [f"T{i:09d}" for i in range(1, n + 1)],
        "account_id": acc_ids,
        "txn_timestamp": timestamps,
        "txn_type": txn_types,
        "amount": amounts,
        "currency": currencies,
        "merchant_category": rng.choice(MERCHANT_CATEGORIES, size=n),
        "channel": rng.choice(CHANNELS, size=n),
        "status": rng.choice(STATUSES, size=n, p=[0.92, 0.04, 0.03, 0.01]),
    })
    # Only card-style payments have a merchant category
    df.loc[~df["txn_type"].isin(["PAYMENT", "WITHDRAWAL"]), "merchant_category"] = None
    return df.sort_values("txn_timestamp").reset_index(drop=True)


def inject_dirty_data(customers, accounts, transactions):
    """Add realistic bronze-layer problems for the cleaning stage to fix."""
    customers.loc[customers.sample(frac=0.03, random_state=1).index, "email"] = None
    customers.loc[customers.sample(frac=0.02, random_state=2).index, "phone"] = None
    idx = customers.sample(frac=0.03, random_state=3).index
    customers.loc[idx, "first_name"] = customers.loc[idx, "first_name"].str.upper()
    customers = pd.concat([customers, customers.sample(frac=0.01, random_state=4)], ignore_index=True)

    idx = accounts.sample(frac=0.03, random_state=5).index
    accounts.loc[idx, "status"] = accounts.loc[idx, "status"].str.lower()
    accounts.loc[accounts.sample(frac=0.01, random_state=6).index, "balance"] *= -1

    transactions.loc[transactions.sample(frac=0.01, random_state=7).index, "amount"] = None
    transactions.loc[transactions.sample(frac=0.005, random_state=8).index, "amount"] *= -1
    idx = transactions.sample(frac=0.02, random_state=9).index
    transactions.loc[idx, "status"] = transactions.loc[idx, "status"].str.title()
    transactions.loc[transactions.sample(frac=0.003, random_state=10).index, "account_id"] = "A9999999"
    transactions = pd.concat(
        [transactions, transactions.sample(frac=0.01, random_state=11)], ignore_index=True
    )
    return customers, accounts, transactions


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic banking data.")
    parser.add_argument("--customers", type=int, default=1000)
    parser.add_argument("--transactions", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clean", action="store_true", help="skip injecting data-quality issues")
    args = parser.parse_args()

    Faker.seed(args.seed)
    fake = Faker()
    rng = np.random.default_rng(args.seed)

    customers = make_customers(fake, rng, args.customers)
    accounts = make_accounts(rng, customers)
    transactions = make_transactions(rng, accounts, args.transactions)

    if not args.clean:
        customers, accounts, transactions = inject_dirty_data(customers, accounts, transactions)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    customers.to_csv(OUT_DIR / "customers.csv", index=False)
    accounts.to_csv(OUT_DIR / "accounts.csv", index=False)
    transactions.to_csv(OUT_DIR / "transactions.csv", index=False)

    print(f"Wrote to {OUT_DIR}")
    print(f"  customers.csv     {len(customers):>8,} rows")
    print(f"  accounts.csv      {len(accounts):>8,} rows")
    print(f"  transactions.csv  {len(transactions):>8,} rows")
    if args.clean:
        print("Data is clean (no injected issues).")
    else:
        print("Injected issues: nulls, duplicates, negative amounts, casing, orphan account IDs.")


if __name__ == "__main__":
    main()