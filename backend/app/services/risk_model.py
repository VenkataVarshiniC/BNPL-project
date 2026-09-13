"""
Runtime wrapper around the trained default-risk model.
Loads once (module-level singleton) and exposes simple scoring functions
used by the risk, optimization, and explainability routers.
"""
import json
import pickle
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import sklearn

from app.config import settings
from app.ml.train_model import NUMERIC_FEATURES, CATEGORICAL_FEATURES


class ModelVersionMismatchError(RuntimeError):
    """Raised when risk_model.pkl was trained with a different scikit-learn
    version than the one currently installed. Pickled sklearn/numpy objects
    are NOT guaranteed compatible across versions — the fix is always to
    retrain locally, never to force-load an incompatible file."""


class ModelFileCorruptError(RuntimeError):
    """Raised when risk_model.pkl exists but is empty or truncated — almost
    always caused by uvicorn --reload restarting the server while
    train_model.py was still writing the file (a torn write)."""


@lru_cache(maxsize=1)
def get_model():
    if not settings.model_file.exists():
        raise FileNotFoundError(
            f"Model not found at {settings.model_file}. "
            f"Run `python -m app.ml.train_model` first."
        )

    file_size = settings.model_file.stat().st_size
    if file_size == 0:
        raise ModelFileCorruptError(
            f"{settings.model_file} is 0 bytes — it's empty, not just outdated. "
            f"This happens when `uvicorn --reload` restarts the server while "
            f"`python -m app.ml.train_model` is still writing the file. "
            f"Fix: stop the server completely, re-run "
            f"`python -m app.ml.train_model` to completion (wait for "
            f"'Saved model -> ...' in the console), THEN start uvicorn. "
            f"If you use --reload, exclude app/ml and app/data from the watcher: "
            f"`uvicorn app.main:app --reload --reload-exclude 'app/data/*' "
            f"--reload-exclude 'app/ml/*' --port 8000`"
        )

    try:
        return joblib.load(settings.model_file)
    except (EOFError, pickle.UnpicklingError, ValueError, AttributeError, ModuleNotFoundError) as e:
        if isinstance(e, EOFError) or "truncat" in str(e).lower():
            raise ModelFileCorruptError(
                f"{settings.model_file} is truncated (file exists, {file_size} bytes, "
                f"but is incomplete/corrupt: {e}). This happens when `uvicorn --reload` "
                f"restarts the server mid-write while `python -m app.ml.train_model` "
                f"was still saving the file. "
                f"Fix: stop the server completely, delete app/ml/risk_model.pkl and "
                f"app/ml/feature_meta.json, re-run "
                f"`python -m app.data.generate_synthetic_data` then "
                f"`python -m app.ml.train_model` and wait for it to fully finish, "
                f"THEN start uvicorn. To prevent recurrence, exclude app/ml and "
                f"app/data from the reload watcher: "
                f"`uvicorn app.main:app --reload --reload-exclude 'app/data/*' "
                f"--reload-exclude 'app/ml/*' --port 8000`"
            ) from e
        raise ModelVersionMismatchError(
            f"Failed to load {settings.model_file} — this almost always means it was "
            f"trained with a different scikit-learn/numpy version than the one currently "
            f"installed (you have scikit-learn {sklearn.__version__}). "
            f"Fix: delete app/ml/risk_model.pkl and app/ml/feature_meta.json, then run "
            f"`python -m app.data.generate_synthetic_data` followed by "
            f"`python -m app.ml.train_model` to retrain against your installed versions. "
            f"Original error: {e}"
        ) from e


@lru_cache(maxsize=1)
def get_feature_meta() -> dict:
    with open(settings.feature_meta_file) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_oof_scores() -> np.ndarray:
    """Out-of-fold default probabilities, aligned row-for-row with
    transactions.csv in its on-disk order.

    Used by the strategy simulator instead of in-sample predictions. Each
    score was produced by a model fold that never saw that row during
    training, so the simulated approved subset reflects how the policy
    would behave on unseen applications rather than on rows the model has
    already memorised.
    """
    if not settings.oof_scores_file.exists():
        raise FileNotFoundError(
            f"Out-of-fold scores not found at {settings.oof_scores_file}. "
            f"Run `python -m app.ml.train_model` first — it computes and "
            f"persists them alongside the model."
        )
    return np.load(settings.oof_scores_file)


def score_dataframe(feature_df: pd.DataFrame) -> np.ndarray:
    """feature_df must contain NUMERIC_FEATURES + CATEGORICAL_FEATURES columns."""
    model = get_model()
    cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    return model.predict_proba(feature_df[cols])[:, 1]


def score_single(
    age: float, income: float, credit_score: float,
    transaction_amount: float, num_installments: int,
    merchant_category: str, employment_status: str, region: str,
) -> float:
    row = pd.DataFrame([{
        "transaction_amount": transaction_amount,
        "num_installments": num_installments,
        "age": age,
        "income": income,
        "credit_score": credit_score,
        "merchant_category": merchant_category,
        "employment_status": employment_status,
        "region": region,
    }])
    return float(score_dataframe(row)[0])


def risk_tier(probability: float) -> tuple[str, str]:
    if probability < 0.15:
        return "Low", "Approve"
    if probability < 0.35:
        return "Medium", "Approve with standard terms"
    if probability < 0.55:
        return "High", "Approve with reduced limit / shorter installment plan"
    return "Very high", "Decline or require manual underwriting review"