"""
Loads customers.csv / transactions.csv into memory once and
serves cached DataFrames + a merged view to the rest of the app.
"""
from functools import lru_cache
import pandas as pd
from app.config import settings


@lru_cache(maxsize=1)
def get_customers() -> pd.DataFrame:
    df = pd.read_csv(settings.customers_file, parse_dates=["signup_date"])
    return df


@lru_cache(maxsize=1)
def get_transactions() -> pd.DataFrame:
    df = pd.read_csv(settings.transactions_file, parse_dates=["transaction_date"])
    return df


@lru_cache(maxsize=1)
def get_merged() -> pd.DataFrame:
    customers = get_customers()
    transactions = get_transactions()
    return transactions.merge(customers, on="customer_id", how="left")


def reload_data():
    """Clears cache — call after regenerating synthetic data."""
    get_customers.cache_clear()
    get_transactions.cache_clear()
    get_merged.cache_clear()
