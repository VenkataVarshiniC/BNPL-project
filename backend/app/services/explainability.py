"""
Produces per-prediction SHAP explanations so a risk score is never a
black-box number — every prediction can show which factors pushed it
up or down, which is what a real credit decision needs to be defensible.
"""
import numpy as np
import pandas as pd
import shap

from app.services.risk_model import get_model, NUMERIC_FEATURES, CATEGORICAL_FEATURES


def _get_transformed_feature_names(preprocessor) -> list[str]:
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_names = list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    # remainder="passthrough" appends numeric columns in original order after transformed ones
    return cat_names + NUMERIC_FEATURES


def explain_row(feature_row: pd.DataFrame, top_n: int = 8) -> dict:
    """feature_row: single-row DataFrame with NUMERIC_FEATURES + CATEGORICAL_FEATURES."""
    pipeline = get_model()
    preprocessor = pipeline.named_steps["preprocess"]
    gbm = pipeline.named_steps["model"]

    cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X_transformed = preprocessor.transform(feature_row[cols])
    if hasattr(X_transformed, "toarray"):
        X_transformed = X_transformed.toarray()

    explainer = shap.TreeExplainer(gbm)
    shap_values = explainer.shap_values(X_transformed)

    # binary classifier: shap_values may be array (n_samples, n_features) for class 1
    if isinstance(shap_values, list):
        values = np.array(shap_values[1][0])
        base_value = float(np.array(explainer.expected_value[1]).ravel()[0])
    else:
        values = np.array(shap_values[0])
        base_value = float(np.array(explainer.expected_value).ravel()[0])

    feature_names = _get_transformed_feature_names(preprocessor)
    raw_values = X_transformed[0]

    contributions = sorted(
        zip(feature_names, raw_values, values),
        key=lambda t: abs(t[2]),
        reverse=True,
    )[:top_n]

    probability = float(pipeline.predict_proba(feature_row[cols])[:, 1][0])

    return {
        "default_probability": round(probability, 4),
        "base_value": round(base_value, 4),
        "top_contributions": [
            {
                "feature": name,
                "value": round(float(val), 4),
                "shap_contribution": round(float(contrib), 4),
            }
            for name, val, contrib in contributions
        ],
    }
