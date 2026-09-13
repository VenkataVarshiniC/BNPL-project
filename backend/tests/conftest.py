"""Shared fixtures.

The financial tests deliberately use small hand-built portfolios whose
expected revenue, loss and profit can be computed by hand and written into
the assertion. Tests that assert against the real 42,000-row dataset would
only confirm that the code agrees with itself.
"""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def tiny_transactions() -> pd.DataFrame:
    """Six transactions with hand-computable economics.

    fee_revenue total                     = 10 + 20 + 30 + 40 + 50 + 60 = 210
    defaulted principal (rows 2, 4, 6)    = 200 + 400 + 600            = 1200
    at LGD 0.65 -> losses                 = 780
    net profit                            = 210 - 780                  = -570
    """
    return pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(1, 7)],
        "customer_id": [f"C{i}" for i in range(1, 7)],
        "merchant_category": ["Travel", "Travel", "Groceries",
                              "Groceries", "Electronics", "Electronics"],
        "transaction_amount": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
        "fee_revenue": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "num_installments": [2, 3, 4, 2, 3, 4],
        "is_default": [0, 1, 0, 1, 0, 1],
        "credit_score": [700, 550, 720, 580, 690, 500],
    })


@pytest.fixture
def tiny_customers() -> pd.DataFrame:
    return pd.DataFrame({
        "customer_id": [f"C{i}" for i in range(1, 7)],
        "income": [50_000.0] * 6,
        "credit_score": [700, 550, 720, 580, 690, 500],
    })


@pytest.fixture
def perfect_scores() -> np.ndarray:
    """Scores that rank the tiny portfolio perfectly: defaulters score high."""
    return np.array([0.01, 0.90, 0.02, 0.80, 0.03, 0.95])


@pytest.fixture
def legacy_stub() -> dict:
    return {"approval_rate_pct": 80.0, "projected_net_profit": -1000.0}
