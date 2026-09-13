from fastapi import APIRouter, Query

from app.config import settings
from app.data.loader import get_merged, get_transactions
from app.models.schemas import OptimizationResponse
from app.services.risk_model import get_oof_scores
from app.services.analytics_engine import (
    approve_all_baseline,
    build_strategy_ladder,
    default_threshold_grid,
    legacy_policy_baseline,
    simulate_thresholds,
)

router = APIRouter(prefix="/api/optimization", tags=["Optimization"])


@router.get("/thresholds", response_model=OptimizationResponse)
def get_threshold_optimization(
    lgd: float = Query(
        None, ge=0.0, le=1.0,
        description="Loss given default — share of principal unrecovered on "
                    "default. Defaults to the configured assumption.",
    ),
    min_approval_rate_pct: float = Query(
        None, ge=0.0, le=100.0,
        description="Minimum share of transactions that must remain approved "
                    "for a strategy to be considered shippable.",
    ),
    credit_score_cutoff: int = Query(
        None, ge=300, le=850,
        description="Credit-score cutoff defining the legacy comparison policy.",
    ),
):
    """
    Risk-adjusted approval strategy simulation.

    Answers: if we approve on predicted default probability instead of on a
    credit-score cutoff, what happens to approval rate, loss rate and profit?

    Three things distinguish this from a naive threshold sweep:

    1. Scores are OUT-OF-FOLD. Every transaction is scored by a model fold
       that never trained on it, so the approved subset is not flattered by
       the model having already seen its outcome.
    2. The grid extends far below any plausible operating point, so an
       optimum resting on the grid boundary is reported as such rather than
       presented as a located maximum.
    3. Two optima are returned — the unconstrained profit maximum, and the
       best threshold that still approves enough of the book to be
       commercially shippable. The recommendation is the constrained one.
    """
    lgd = settings.loss_given_default if lgd is None else lgd
    floor = (
        settings.min_approval_rate_pct
        if min_approval_rate_pct is None
        else min_approval_rate_pct
    )
    cutoff = (
        settings.legacy_credit_score_cutoff
        if credit_score_cutoff is None
        else credit_score_cutoff
    )

    merged = get_merged()
    transactions = get_transactions()
    oof = get_oof_scores()

    simulated = simulate_thresholds(
        transactions, oof, thresholds=default_threshold_grid(), lgd=lgd
    )
    legacy = legacy_policy_baseline(merged, credit_score_cutoff=cutoff, lgd=lgd)
    approve_all = approve_all_baseline(transactions, lgd=lgd)
    ladder = build_strategy_ladder(simulated, legacy, min_approval_rate_pct=floor)

    return OptimizationResponse(
        simulated_points=simulated,
        strategies=ladder["strategies"],
        recommended_strategy=ladder["recommended_strategy"],
        recommended_threshold=ladder["recommended_threshold"],
        recommended_reason=ladder["recommended_reason"],
        min_approval_rate_pct=ladder["min_approval_rate_pct"],
        boundary_optimum=ladder["boundary_optimum"],
        volume_floor_feasible=ladder["volume_floor_feasible"],
        profit_floor=ladder["profit_floor"],
        caveats=ladder["caveats"],
        legacy_baseline=legacy,
        approve_all_baseline=approve_all,
        assumptions={
            "loss_given_default": lgd,
            "legacy_credit_score_cutoff": cutoff,
            "min_approval_rate_pct": floor,
            "scoring": "out-of-fold (cross-validated)",
            "cv_folds": settings.cv_folds,
            "dataset": "synthetic",
        },
    )
