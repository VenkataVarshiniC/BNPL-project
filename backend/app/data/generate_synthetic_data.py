"""
Generates a synthetic but statistically coherent BNPL dataset:
- ~5,000 customers
- ~42,000 transactions

Default risk is deliberately correlated with credit_score, income,
utilization, and num_installments so downstream models have real
signal to learn from (not pure noise).

Run:
    python -m app.data.generate_synthetic_data
"""
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))
from app.config import settings

MERCHANT_CATEGORIES = [
    "Electronics", "Fashion & Apparel", "Home & Furniture", "Beauty & Wellness",
    "Travel", "Groceries", "Sporting Goods", "Jewelry & Accessories",
    "Health & Fitness", "Education",
]

REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
EMPLOYMENT_STATUS = ["Full-time", "Part-time", "Self-employed", "Unemployed", "Student"]

# base fee rate + avg default-loss-severity assumptions per category
CATEGORY_PROFILE = {
    "Electronics":            {"fee_rate": 0.045, "avg_ticket": 420, "risk_mult": 1.15},
    "Fashion & Apparel":      {"fee_rate": 0.055, "avg_ticket": 130, "risk_mult": 1.05},
    "Home & Furniture":       {"fee_rate": 0.040, "avg_ticket": 650, "risk_mult": 1.10},
    "Beauty & Wellness":      {"fee_rate": 0.060, "avg_ticket": 90,  "risk_mult": 0.85},
    "Travel":                 {"fee_rate": 0.035, "avg_ticket": 900, "risk_mult": 1.25},
    "Groceries":              {"fee_rate": 0.030, "avg_ticket": 60,  "risk_mult": 0.60},
    "Sporting Goods":         {"fee_rate": 0.050, "avg_ticket": 180, "risk_mult": 0.95},
    "Jewelry & Accessories":  {"fee_rate": 0.065, "avg_ticket": 350, "risk_mult": 1.30},
    "Health & Fitness":       {"fee_rate": 0.045, "avg_ticket": 150, "risk_mult": 0.80},
    "Education":              {"fee_rate": 0.025, "avg_ticket": 500, "risk_mult": 0.90},
}


def generate_customers(n: int, rng: np.random.Generator) -> pd.DataFrame:
    customer_ids = [f"CUST{100000 + i}" for i in range(n)]
    age = np.clip(rng.normal(34, 10, n), 18, 75).astype(int)
    income = np.clip(rng.lognormal(mean=10.6, sigma=0.45, size=n), 15000, 350000).round(2)
    credit_score = np.clip(rng.normal(660, 75, n), 300, 850).astype(int)
    employment_status = rng.choice(EMPLOYMENT_STATUS, size=n, p=[0.55, 0.15, 0.15, 0.07, 0.08])
    region = rng.choice(REGIONS, size=n)
    signup_days_ago = rng.integers(30, 900, size=n)
    signup_date = pd.Timestamp.today().normalize() - pd.to_timedelta(signup_days_ago, unit="D")

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "age": age,
        "income": income,
        "credit_score": credit_score,
        "employment_status": employment_status,
        "region": region,
        "signup_date": signup_date,
    })
    return df


def generate_transactions(customers: pd.DataFrame, n: int, rng: np.random.Generator) -> pd.DataFrame:
    cust_idx = rng.choice(len(customers), size=n, replace=True,
                           p=_weighted_activity(len(customers), rng))
    cust_sample = customers.iloc[cust_idx].reset_index(drop=True)

    categories = rng.choice(list(CATEGORY_PROFILE.keys()), size=n)
    merchant_ids = [f"MER{1000 + rng.integers(0, 400)}" for _ in range(n)]

    amounts = np.array([
        max(15, rng.normal(CATEGORY_PROFILE[c]["avg_ticket"], CATEGORY_PROFILE[c]["avg_ticket"] * 0.35))
        for c in categories
    ]).round(2)

    num_installments = rng.choice([2, 3, 4, 6, 12], size=n, p=[0.35, 0.30, 0.20, 0.10, 0.05])

    days_ago = rng.integers(0, 365, size=n)
    transaction_date = pd.Timestamp.today().normalize() - pd.to_timedelta(days_ago, unit="D")

    fee_rate = np.array([CATEGORY_PROFILE[c]["fee_rate"] for c in categories])
    fee_revenue = (amounts * fee_rate).round(2)

    # ---- default probability model (ground truth generator) ----
    credit_component = (750 - cust_sample["credit_score"].values) / 450.0
    income_component = np.clip(1 - (cust_sample["income"].values / 120000), -0.3, 0.6)
    installment_component = (num_installments - 2) / 22.0
    category_mult = np.array([CATEGORY_PROFILE[c]["risk_mult"] for c in categories])
    employment_penalty = np.where(cust_sample["employment_status"].values == "Unemployed", 0.18,
                          np.where(cust_sample["employment_status"].values == "Student", 0.05, 0.0))

    category_offset = np.log(category_mult) * 1.4

    base_default_logit = (
        -4.6
        + 4.2 * credit_component
        + 2.0 * income_component
        + 2.2 * installment_component
        + employment_penalty
        + category_offset
    )

    default_prob = 1 / (1 + np.exp(-base_default_logit))
    default_prob = np.clip(default_prob, 0.005, 0.85)
    is_default = rng.binomial(1, default_prob)

    df = pd.DataFrame({
        "transaction_id": [f"TXN{1000000 + i}" for i in range(n)],
        "customer_id": cust_sample["customer_id"].values,
        "merchant_id": merchant_ids,
        "merchant_category": categories,
        "transaction_amount": amounts,
        "num_installments": num_installments,
        "transaction_date": transaction_date,
        "fee_revenue": fee_revenue,
        "is_default": is_default,
        "true_default_probability": default_prob.round(4),
    })
    return df


def _weighted_activity(n_customers: int, rng: np.random.Generator) -> np.ndarray:
    """Some customers transact far more than others (power-law-ish)."""
    weights = rng.pareto(2.5, n_customers) + 0.3
    return weights / weights.sum()


def main():
    rng = np.random.default_rng(settings.random_seed)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    customers = generate_customers(settings.n_customers, rng)
    transactions = generate_transactions(customers, settings.n_transactions, rng)

    customers.to_csv(settings.customers_file, index=False)
    transactions.to_csv(settings.transactions_file, index=False)

    print(f"Wrote {len(customers)} customers -> {settings.customers_file}")
    print(f"Wrote {len(transactions)} transactions -> {settings.transactions_file}")
    print(f"Overall default rate: {transactions['is_default'].mean():.3%}")


if __name__ == "__main__":
    main()
