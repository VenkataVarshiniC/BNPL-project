"""
Deterministic business analytics — no ML here, just aggregation and
rule-based logic. This is the layer that answers "what is happening"
as opposed to risk_model.py which answers "what is likely to happen".

Every function that computes a loss figure takes `lgd` (loss given
default) explicitly rather than hardcoding it, because it is a modelling
assumption the product must be able to vary and report.
"""
import numpy as np
import pandas as pd

from app.config import settings


def _expected_losses(df: pd.DataFrame, lgd: float) -> float:
    """Unrecovered principal on defaulted transactions.

    Loss = defaulted principal x loss-given-default. `lgd` is an
    assumption, not a measurement — see settings.loss_given_default.
    """
    return float(df.loc[df["is_default"] == 1, "transaction_amount"].sum() * lgd)


def _economics(df: pd.DataFrame, lgd: float) -> dict:
    """Fee revenue, expected loss and net profit for any subset of the book."""
    fee_revenue = float(df["fee_revenue"].sum())
    default_losses = _expected_losses(df, lgd)
    return {
        "fee_revenue": fee_revenue,
        "default_losses": default_losses,
        "net_profit": fee_revenue - default_losses,
    }


# ---------- 1. Customer segmentation ----------

def segment_customers(merged: pd.DataFrame) -> pd.DataFrame:
    """
    RFM-style segmentation using quantile bucketing on:
      - total spend (Monetary)
      - transaction count (Frequency)
      - credit_score (proxy for underlying quality)
    Produces 4 business-readable segments.
    """
    agg = merged.groupby("customer_id").agg(
        total_spend=("transaction_amount", "sum"),
        transaction_count=("transaction_id", "count"),
        default_rate=("is_default", "mean"),
        income=("income", "first"),
        credit_score=("credit_score", "first"),
    ).reset_index()

    spend_q = agg["total_spend"].rank(pct=True)
    freq_q = agg["transaction_count"].rank(pct=True)
    quality_q = agg["credit_score"].rank(pct=True)

    score = (spend_q + freq_q + quality_q) / 3

    def label(s):
        if s >= 0.75:
            return "Premium loyalists"
        if s >= 0.5:
            return "Growth potential"
        if s >= 0.25:
            return "Occasional users"
        return "At-risk / low-value"

    agg["segment_name"] = score.apply(label)
    return agg


def summarize_segments(agg: pd.DataFrame) -> list[dict]:
    order = ["Premium loyalists", "Growth potential", "Occasional users", "At-risk / low-value"]
    out = []
    for seg in order:
        sub = agg[agg["segment_name"] == seg]
        if sub.empty:
            continue
        out.append({
            "segment_name": seg,
            "customer_count": int(len(sub)),
            "avg_income": round(float(sub["income"].mean()), 2),
            "avg_credit_score": round(float(sub["credit_score"].mean()), 1),
            "avg_transaction_count": round(float(sub["transaction_count"].mean()), 2),
            "avg_total_spend": round(float(sub["total_spend"].mean()), 2),
            "default_rate": round(float(sub["default_rate"].mean()), 4),
        })
    return out


# ---------- 2. Merchant category profitability ----------

def category_profitability(
    transactions: pd.DataFrame, lgd: float | None = None
) -> list[dict]:
    lgd = settings.loss_given_default if lgd is None else lgd
    grp = transactions.groupby("merchant_category")
    out = []
    for cat, sub in grp:
        volume = sub["transaction_amount"].sum()
        econ = _economics(sub, lgd)
        fee_revenue = econ["fee_revenue"]
        default_losses = econ["default_losses"]
        net_profit = econ["net_profit"]
        out.append({
            "merchant_category": cat,
            "transaction_count": int(len(sub)),
            "total_volume": round(float(volume), 2),
            "total_fee_revenue": round(float(fee_revenue), 2),
            "total_default_losses": round(float(default_losses), 2),
            "net_profit": round(float(net_profit), 2),
            "profit_margin_pct": round(float(net_profit / volume * 100), 2) if volume else 0.0,
            "default_rate": round(float(sub["is_default"].mean()), 4),
        })
    out.sort(key=lambda r: r["net_profit"], reverse=True)
    return out


# ---------- 3. Portfolio-level profitability ----------

def portfolio_metrics(
    customers: pd.DataFrame, transactions: pd.DataFrame, lgd: float | None = None
) -> dict:
    lgd = settings.loss_given_default if lgd is None else lgd
    volume = float(transactions["transaction_amount"].sum())
    econ = _economics(transactions, lgd)
    net_profit = econ["net_profit"]

    return {
        "total_customers": int(customers["customer_id"].nunique()),
        "total_transactions": int(len(transactions)),
        "total_volume": round(volume, 2),
        "total_fee_revenue": round(econ["fee_revenue"], 2),
        "total_default_losses": round(econ["default_losses"], 2),
        "net_profit": round(net_profit, 2),
        "overall_default_rate": round(float(transactions["is_default"].mean()), 4),
        "profit_margin_pct": round(net_profit / volume * 100, 2) if volume else 0.0,
        "loss_given_default": lgd,
    }


# ---------- 3b. Policy baselines ----------

def approve_all_baseline(transactions: pd.DataFrame, lgd: float | None = None) -> dict:
    """The weakest possible comparator: approve every application.

    Retained because it isolates the gross economics of the book, but it
    is NOT a lending policy any real BNPL operates, and it should never
    be the headline comparator for an improvement claim.
    """
    lgd = settings.loss_given_default if lgd is None else lgd
    econ = _economics(transactions, lgd)
    return {
        "policy_name": "Approve all (reference only)",
        "policy_type": "reference",
        "description": (
            "Every application approved. Not a real lending policy — included "
            "to isolate the gross economics of the book."
        ),
        "approval_rate_pct": 100.0,
        "approved_count": int(len(transactions)),
        "approved_default_rate": round(float(transactions["is_default"].mean()), 4),
        "projected_fee_revenue": round(econ["fee_revenue"], 2),
        "projected_default_losses": round(econ["default_losses"], 2),
        "projected_net_profit": round(econ["net_profit"], 2),
    }


def legacy_policy_baseline(
    merged: pd.DataFrame,
    credit_score_cutoff: int | None = None,
    lgd: float | None = None,
) -> dict:
    """The realistic comparator: a credit-score cutoff with no risk adjustment.

    This is the policy the project argues against. It approves on credit
    score alone and ignores installment count, merchant category and
    employment status — all of which carry default signal. The gap between
    this policy and a risk-adjusted one at the SAME approval rate is the
    'risk-adjustment gap', and it is the only improvement figure that is
    not confounded by simply shrinking the book.
    """
    cutoff = (
        settings.legacy_credit_score_cutoff
        if credit_score_cutoff is None
        else credit_score_cutoff
    )
    lgd = settings.loss_given_default if lgd is None else lgd

    approved = merged[merged["credit_score"] >= cutoff]
    econ = _economics(approved, lgd)
    return {
        "policy_name": f"Legacy policy — credit score >= {cutoff}",
        "policy_type": "baseline",
        "description": (
            f"Approve if credit score >= {cutoff}. Ignores installment count, "
            f"merchant category and employment status, all of which carry "
            f"default signal. This is the current-state policy."
        ),
        "credit_score_cutoff": cutoff,
        "approval_rate_pct": round(len(approved) / len(merged) * 100, 2),
        "approved_count": int(len(approved)),
        "approved_default_rate": round(float(approved["is_default"].mean()), 4)
        if len(approved)
        else 0.0,
        "projected_fee_revenue": round(econ["fee_revenue"], 2),
        "projected_default_losses": round(econ["default_losses"], 2),
        "projected_net_profit": round(econ["net_profit"], 2),
    }


# ---------- 4. Risk-adjusted threshold optimization ----------

def default_threshold_grid(
    lo: float | None = None, hi: float | None = None
) -> list[float]:
    """Candidate approval thresholds.

    Deliberately finer and far lower at the bottom end than any plausible
    operating point. The original grid started at 0.05 and 0.05 won, which
    meant the reported optimum was sitting on the grid boundary with profit
    still rising — indistinguishable from an unsearched region. Extending
    below it is what makes a boundary optimum detectable.
    """
    lo = settings.threshold_grid_min if lo is None else lo
    hi = settings.threshold_grid_max if hi is None else hi
    # Resolution is concentrated where the profit curve actually turns
    # (roughly 0.02-0.15). Coarse steps out in the tail, where every
    # threshold approves essentially the whole book and profit is flat.
    segments = [
        (lo, min(0.15, hi), 0.0025),
        (0.15, min(0.30, hi), 0.01),
        (0.30, hi, 0.05),
    ]
    grid: list[float] = []
    for seg_lo, seg_hi, step in segments:
        if seg_hi > seg_lo:
            grid.extend(np.arange(seg_lo, seg_hi, step))
    return sorted({round(float(t), 4) for t in grid})


def simulate_thresholds(
    transactions: pd.DataFrame,
    predicted_probs: np.ndarray,
    thresholds: list[float] | None = None,
    lgd: float | None = None,
) -> list[dict]:
    """
    For each candidate approval threshold t: approve transactions where
    predicted default probability <= t, then project profit on the
    approved subset. Lets us trade off approval rate vs. loss rate.

    `predicted_probs` MUST be out-of-fold predictions. Scoring with a model
    that trained on these rows makes the approved subset look cleaner than
    an unseen application population would, which inflates projected profit.
    """
    if len(predicted_probs) != len(transactions):
        raise ValueError(
            f"predicted_probs has {len(predicted_probs)} entries but "
            f"transactions has {len(transactions)} rows — they must align."
        )
    if thresholds is None:
        thresholds = default_threshold_grid()
    lgd = settings.loss_given_default if lgd is None else lgd

    df = transactions.copy()
    df["pred_default_prob"] = predicted_probs

    total_n = len(df)
    total_volume = float(df["transaction_amount"].sum())
    results = []
    for t in thresholds:
        approved = df[df["pred_default_prob"] <= t]
        if approved.empty:
            continue
        econ = _economics(approved, lgd)
        approved_volume = float(approved["transaction_amount"].sum())
        results.append({
            "approval_threshold": t,
            "approval_rate_pct": round(len(approved) / total_n * 100, 2),
            "volume_retained_pct": round(approved_volume / total_volume * 100, 2)
            if total_volume else 0.0,
            "approved_count": int(len(approved)),
            "approved_default_rate": round(float(approved["is_default"].mean()), 4),
            "projected_net_profit": round(econ["net_profit"], 2),
            "projected_fee_revenue": round(econ["fee_revenue"], 2),
            "projected_default_losses": round(econ["default_losses"], 2),
        })
    return results


def build_strategy_ladder(
    simulated_points: list[dict],
    legacy: dict,
    min_approval_rate_pct: float | None = None,
) -> dict:
    """Four named strategies spanning the profit/volume trade-off.

    A single "optimal threshold" hides the decision rather than supporting
    it. Maximising profit alone drives approvals down to roughly a third of
    the book, which no BNPL lender would ship — its economics depend on
    merchant relationships and growth, not on lending as little as possible.

    So the simulation reports a ladder, and recommends by an objective that
    a business can actually defend:

        maximise approved volume, subject to not losing money.

      - volume_matched   : risk-adjusted scoring at the legacy policy's own
                           approval rate. Isolates the value of better
                           selection from the value of simply lending less.
      - breakeven        : the highest approval rate that is still
                           profitable. THE RECOMMENDATION.
      - constrained_max  : most profitable threshold meeting a volume floor.
      - unconstrained_max: most profitable threshold at any volume. Reported
                           as a labelled upper bound, not a recommendation.
    """
    floor = (
        settings.min_approval_rate_pct
        if min_approval_rate_pct is None
        else min_approval_rate_pct
    )

    empty = {
        "strategies": {},
        "recommended_strategy": None,
        "recommended_threshold": None,
        "recommended_reason": "No simulation data available.",
        "min_approval_rate_pct": floor,
        "boundary_optimum": False,
        "caveats": ["Simulation produced no points."],
    }
    if not simulated_points:
        return empty

    unconstrained = max(simulated_points, key=lambda r: r["projected_net_profit"])

    eligible = [p for p in simulated_points if p["approval_rate_pct"] >= floor]
    constrained = (
        max(eligible, key=lambda r: r["projected_net_profit"]) if eligible else None
    )

    # "Break even" means clearing a profit floor, and the floor is not always
    # zero. If the current policy is already profitable, a strategy that
    # merely reaches zero is a step backwards — so the floor is whichever is
    # higher: zero, or what the business already earns today.
    profit_floor = max(0.0, legacy["projected_net_profit"])
    viable = [p for p in simulated_points if p["projected_net_profit"] >= profit_floor]
    breakeven = (
        max(viable, key=lambda r: r["approval_rate_pct"]) if viable else None
    )
    floor_is_legacy = profit_floor > 0

    volume_matched = threshold_at_approval_rate(
        simulated_points, legacy["approval_rate_pct"]
    )

    lowest = min(p["approval_threshold"] for p in simulated_points)
    highest = max(p["approval_threshold"] for p in simulated_points)
    boundary_optimum = unconstrained["approval_threshold"] in (lowest, highest)

    def _entry(point, name, label, rationale):
        if point is None:
            return None
        # Shippability is a property of the resulting approval rate, not of
        # which rule produced the point. When the unconstrained optimum
        # happens to clear the volume floor, it says so.
        return {
            **point,
            "strategy_key": name,
            "strategy_label": label,
            "meets_volume_floor": point["approval_rate_pct"] >= floor,
            "rationale": rationale,
            "profit_vs_legacy": round(
                point["projected_net_profit"] - legacy["projected_net_profit"], 2
            ),
            "approval_rate_change_pp": round(
                point["approval_rate_pct"] - legacy["approval_rate_pct"], 2
            ),
        }

    strategies = {
        "volume_matched": _entry(
            volume_matched, "volume_matched", "Risk-adjusted at current volume",
            "Replaces the credit-score cutoff with model scoring while holding the "
            "approval rate at today's level. The entire gain is attributable to "
            "better selection, with no reduction in lending volume.",
        ),
        "breakeven": _entry(
            breakeven, "breakeven",
            "Maximum volume at no worse than current profit" if floor_is_legacy
            else "Maximum volume at break-even",
            (
                f"The highest approval rate that still earns at least the "
                f"${profit_floor:,.0f} the current policy earns today. Recommended: "
                f"it buys the largest possible book without giving up profit."
            ) if floor_is_legacy else (
                "The highest approval rate at which the book is no longer losing "
                "money. Recommended: it is the least disruptive policy change that "
                "stops the loss."
            ),
        ),
        "constrained_max": _entry(
            constrained, "constrained_max", f"Most profitable above {floor}% approval",
            f"The most profitable threshold that still approves at least {floor}% of "
            f"transactions.",
        ),
        "unconstrained_max": _entry(
            unconstrained, "unconstrained_max", "Maximum profit (any volume)",
            "The profit-maximising threshold with no volume constraint. Reported as "
            "an upper bound only — the approval rate it implies would not be shipped "
            "by a lender whose economics depend on merchant relationships and growth.",
        ),
    }
    strategies = {k: v for k, v in strategies.items() if v is not None}

    caveats = [
        "Projected under modelled assumptions on a synthetic portfolio — not a "
        "measured, realised or audited result.",
        "Approval decisions use out-of-fold model scores; losses on the approved "
        "subset use actual outcomes. This is a backtest, not a forward forecast.",
        f"All loss figures are conditional on a {settings.loss_given_default:.0%} "
        f"loss-given-default assumption.",
    ]
    if boundary_optimum:
        caveats.append(
            f"The unconstrained optimum sits at threshold "
            f"{unconstrained['approval_threshold']}, on the edge of the search grid — "
            f"treat it as a grid artifact rather than a located optimum."
        )
    if breakeven is None:
        caveats.append(
            f"No threshold on the grid clears the ${profit_floor:,.0f} profit floor. "
            f"Decline-only policy is insufficient on these assumptions; risk-based "
            f"pricing or installment-term limits would be required."
        )
    if constrained is not None and constrained["projected_net_profit"] < 0:
        caveats.append(
            f"The {floor}% volume floor cannot be met profitably — the most "
            f"profitable threshold meeting it still loses "
            f"${abs(constrained['projected_net_profit']):,.0f}."
        )

    if breakeven is not None:
        rec_key, rec = "breakeven", strategies["breakeven"]
        movement = (
            f"moves the book from a "
            f"${abs(legacy['projected_net_profit']):,.0f} projected loss to "
            f"${rec['projected_net_profit']:,.0f}"
            if legacy["projected_net_profit"] < 0
            else f"holds projected profit at ${rec['projected_net_profit']:,.0f} "
                 f"against today's ${legacy['projected_net_profit']:,.0f}"
        )
        criterion = (
            "It is the highest approval rate at which the portfolio is not losing "
            "money, so it stops the loss with the smallest reduction in lending "
            "volume."
            if not floor_is_legacy
            else "It is the highest approval rate that gives up no profit against "
                 "the current policy."
        )
        reason = (
            f"Recommended: approval threshold {rec['approval_threshold']}. This "
            f"approves {rec['approval_rate_pct']}% of transactions "
            f"({rec['approval_rate_change_pp']:+.2f}pp against the current "
            f"{legacy['approval_rate_pct']}% policy) and {movement} — a "
            f"${rec['profit_vs_legacy']:,.0f} projected improvement. {criterion} "
            f"Maximum achievable profit is "
            f"${unconstrained['projected_net_profit']:,.0f} at threshold "
            f"{unconstrained['approval_threshold']}, but that approves only "
            f"{unconstrained['approval_rate_pct']}% of the book and is not "
            f"recommended."
        )
    else:
        rec_key, rec = None, None
        reason = (
            "No threshold on the simulated grid produces a profitable book. On these "
            "assumptions, tightening approvals alone cannot restore profitability — "
            "risk-based pricing or installment-term limits would be required."
        )

    return {
        "strategies": strategies,
        "recommended_strategy": rec_key,
        "recommended_threshold": rec["approval_threshold"] if rec else None,
        "recommended_reason": reason,
        "min_approval_rate_pct": floor,
        "boundary_optimum": boundary_optimum,
        # False when the volume floor and the profit floor cannot both be
        # satisfied. That conflict is the headline finding on this portfolio,
        # not an error: it says decline-only policy cannot fix the book
        # without giving up more volume than the business wants to give up.
        "volume_floor_feasible": bool(
            breakeven is not None and breakeven["approval_rate_pct"] >= floor
        ),
        "profit_floor": round(profit_floor, 2),
        "caveats": caveats,
    }


def recommend_threshold(
    simulated_points: list[dict],
    legacy: dict | None = None,
    min_approval_rate_pct: float | None = None,
) -> dict:
    """Backwards-compatible wrapper around build_strategy_ladder."""
    if legacy is None:
        legacy = {"approval_rate_pct": 100.0, "projected_net_profit": 0.0}
    return build_strategy_ladder(
        simulated_points, legacy, min_approval_rate_pct=min_approval_rate_pct
    )


def threshold_at_approval_rate(
    simulated_points: list[dict], target_approval_rate_pct: float
) -> dict | None:
    """The simulated point whose approval rate is closest to a target.

    Used for like-for-like comparison: holding approval rate constant
    against the legacy policy isolates the value of risk adjustment from
    the value of simply lending less.
    """
    if not simulated_points:
        return None
    return min(
        simulated_points,
        key=lambda r: abs(r["approval_rate_pct"] - target_approval_rate_pct),
    )
