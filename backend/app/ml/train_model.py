"""
Trains the default-risk classifier on the synthetic transaction data
and persists it + its feature schema for the API to load at runtime.

Run:
    python -m app.ml.train_model
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split, cross_val_predict, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

sys.path.append(str(Path(__file__).resolve().parents[2]))
from app.config import settings

NUMERIC_FEATURES = [
    "transaction_amount", "num_installments", "age", "income", "credit_score",
]
CATEGORICAL_FEATURES = ["merchant_category", "employment_status", "region"]
TARGET = "is_default"


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ], remainder="passthrough")

    model = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.08,
        random_state=settings.random_seed,
    )

    return Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", model),
    ])


def main():
    customers = pd.read_csv(settings.customers_file)
    transactions = pd.read_csv(settings.transactions_file)
    df = transactions.merge(customers, on="customer_id", how="left")

    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X = df[feature_cols]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=settings.random_seed, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    probs = pipeline.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, probs)
    print(f"Holdout AUC: {auc:.4f}")

    # ------------------------------------------------------------------
    # Out-of-fold scores for honest strategy simulation.
    #
    # The threshold simulation asks "if we had declined transactions the
    # model scores above t, what would profit have been?". Answering that
    # with in-sample predictions is leakage: the model has already seen
    # the outcomes of most rows, so the approved subset looks cleaner than
    # a genuinely unseen application population would.
    #
    # cross_val_predict gives every row a prediction made by a model that
    # never saw it during training, which is the correct counterfactual.
    # Computed once here and persisted, because it costs cv_folds full
    # trainings and must not run per request.
    # ------------------------------------------------------------------
    print(f"Computing {settings.cv_folds}-fold out-of-fold scores "
          f"({len(X):,} rows)...")
    cv = StratifiedKFold(
        n_splits=settings.cv_folds, shuffle=True, random_state=settings.random_seed
    )
    oof = cross_val_predict(
        build_pipeline(), X, y, cv=cv, method="predict_proba", n_jobs=-1
    )[:, 1]
    oof_auc = roc_auc_score(y, oof)
    print(f"Out-of-fold AUC: {oof_auc:.4f}")

    settings.model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, settings.model_file)
    np.save(settings.oof_scores_file, oof)
    print(f"Saved out-of-fold scores -> {settings.oof_scores_file}")

    meta = {
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target": TARGET,
        "holdout_auc": round(float(auc), 4),
        "oof_auc": round(float(oof_auc), 4),
        "cv_folds": settings.cv_folds,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_oof": int(len(oof)),
        "sklearn_version": sklearn.__version__,
    }
    with open(settings.feature_meta_file, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Saved model -> {settings.model_file}")
    print(f"Saved feature metadata -> {settings.feature_meta_file}")


if __name__ == "__main__":
    main()
