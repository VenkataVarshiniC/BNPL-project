from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "BNPL Profitability & Risk API"
    debug: bool = True

    base_dir: Path = Path(__file__).resolve().parent
    data_dir: Path = base_dir / "data"
    model_dir: Path = base_dir / "ml"

    customers_file: Path = data_dir / "customers.csv"
    transactions_file: Path = data_dir / "transactions.csv"
    model_file: Path = model_dir / "risk_model.pkl"
    feature_meta_file: Path = model_dir / "feature_meta.json"

    oof_scores_file: Path = model_dir / "oof_scores.npy"

    n_customers: int = 5000
    n_transactions: int = 42000
    random_seed: int = 42

    # ------------------------------------------------------------------
    # Economic assumptions
    #
    # These are MODELLING ASSUMPTIONS, not measured values. Every profit
    # and loss figure the product reports is conditional on them, so they
    # are declared here rather than buried in the analytics code, and the
    # API surfaces them alongside every result.
    # ------------------------------------------------------------------

    # Loss given default: the share of transaction principal that is
    # unrecovered when a customer defaults. Industry BNPL recovery rates
    # vary widely; 0.65 LGD (i.e. 35% recovered) is a mid-range assumption.
    # Sensitivity is material — see /api/optimization/sensitivity.
    loss_given_default: float = 0.65

    # Legacy underwriting policy used as the realistic comparison baseline:
    # approve if credit score is at or above this cutoff, ignoring
    # installment count, merchant category and employment status. This is
    # the "risk-adjustment gap" the project investigates.
    legacy_credit_score_cutoff: int = 600

    # Minimum share of transaction volume that must remain approved for a
    # strategy to be considered commercially shippable. An unconstrained
    # profit optimum that declines most of the book destroys merchant
    # relationships and growth, so recommendations are reported both
    # unconstrained and subject to this floor.
    min_approval_rate_pct: float = 75.0

    # Threshold search grid. The lower bound is deliberately far below any
    # plausible operating point so that a recommendation sitting on the
    # boundary is detectable rather than silently accepted.
    threshold_grid_min: float = 0.005
    threshold_grid_max: float = 0.65

    # Folds used for out-of-fold scoring in the strategy simulation.
    cv_folds: int = 5

    class Config:
        env_file = ".env"
        protected_namespaces = ("settings_",)
        # A stray or misspelled key in .env should not stop the application
        # from starting. Pydantic's default is to reject unknown inputs, which
        # turns a typo in an optional config file into a crash at import time,
        # before any error handler exists to explain it.
        extra = "ignore"


settings = Settings()
