"""Financial-logic tests.

Every expected value here is computed by hand from the fixture, not copied
from a program run. None of these tests assert the $70K / $400K headline
figures — those are outputs of the model, and pinning them in a test would
convert a reproducible result into a hardcoded one.
"""
import numpy as np
import pandas as pd
import pytest

from app.services import analytics_engine as ae


# ---------------------------------------------------------------- revenue

def test_fee_revenue_is_the_sum_of_the_column(tiny_transactions):
    econ = ae._economics(tiny_transactions, lgd=0.65)
    assert econ["fee_revenue"] == pytest.approx(210.0)


def test_fee_revenue_ignores_default_status(tiny_transactions):
    """Fees are earned at transaction time; a later default does not claw
    them back under this model. Changing that would be a model change, so
    it is asserted explicitly rather than left implicit."""
    all_good = tiny_transactions.assign(is_default=0)
    all_bad = tiny_transactions.assign(is_default=1)
    assert (
        ae._economics(all_good, 0.65)["fee_revenue"]
        == ae._economics(all_bad, 0.65)["fee_revenue"]
        == pytest.approx(210.0)
    )


# ------------------------------------------------------------------ losses

def test_expected_loss_is_defaulted_principal_times_lgd(tiny_transactions):
    # defaulted principal = 200 + 400 + 600 = 1200
    assert ae._expected_losses(tiny_transactions, lgd=0.65) == pytest.approx(780.0)
    assert ae._expected_losses(tiny_transactions, lgd=1.0) == pytest.approx(1200.0)
    assert ae._expected_losses(tiny_transactions, lgd=0.0) == pytest.approx(0.0)


def test_expected_loss_scales_linearly_with_lgd(tiny_transactions):
    half = ae._expected_losses(tiny_transactions, lgd=0.30)
    full = ae._expected_losses(tiny_transactions, lgd=0.60)
    assert full == pytest.approx(2 * half)


def test_no_defaults_means_no_losses(tiny_transactions):
    clean = tiny_transactions.assign(is_default=0)
    assert ae._expected_losses(clean, lgd=0.65) == pytest.approx(0.0)


# ------------------------------------------------------------------ profit

def test_net_profit_is_revenue_minus_losses(tiny_transactions):
    econ = ae._economics(tiny_transactions, lgd=0.65)
    assert econ["net_profit"] == pytest.approx(210.0 - 780.0)
    assert econ["net_profit"] == pytest.approx(econ["fee_revenue"] - econ["default_losses"])


def test_profit_is_monotonically_decreasing_in_lgd(tiny_transactions):
    profits = [ae._economics(tiny_transactions, lgd=l)["net_profit"]
               for l in (0.0, 0.25, 0.5, 0.75, 1.0)]
    assert profits == sorted(profits, reverse=True)


# --------------------------------------------------------------- portfolio

def test_portfolio_metrics_reconcile(tiny_customers, tiny_transactions):
    m = ae.portfolio_metrics(tiny_customers, tiny_transactions, lgd=0.65)
    assert m["total_customers"] == 6
    assert m["total_transactions"] == 6
    assert m["total_volume"] == pytest.approx(2100.0)
    assert m["total_fee_revenue"] == pytest.approx(210.0)
    assert m["total_default_losses"] == pytest.approx(780.0)
    assert m["net_profit"] == pytest.approx(-570.0)
    assert m["overall_default_rate"] == pytest.approx(0.5)
    assert m["loss_given_default"] == 0.65


def test_portfolio_margin_matches_profit_over_volume(tiny_customers, tiny_transactions):
    m = ae.portfolio_metrics(tiny_customers, tiny_transactions, lgd=0.65)
    assert m["profit_margin_pct"] == pytest.approx(
        m["net_profit"] / m["total_volume"] * 100, abs=0.01
    )


def test_category_profits_sum_to_portfolio_profit(tiny_customers, tiny_transactions):
    """Guards against double counting or dropped rows in the category split."""
    cats = ae.category_profitability(tiny_transactions, lgd=0.65)
    portfolio = ae.portfolio_metrics(tiny_customers, tiny_transactions, lgd=0.65)
    assert sum(c["net_profit"] for c in cats) == pytest.approx(
        portfolio["net_profit"], abs=0.01
    )
    assert sum(c["transaction_count"] for c in cats) == portfolio["total_transactions"]


# -------------------------------------------------------------- baselines

def test_approve_all_baseline_approves_everything(tiny_transactions):
    b = ae.approve_all_baseline(tiny_transactions, lgd=0.65)
    assert b["approval_rate_pct"] == 100.0
    assert b["approved_count"] == 6
    assert b["projected_net_profit"] == pytest.approx(-570.0)


def test_legacy_policy_applies_the_credit_cutoff(tiny_transactions):
    # credit scores: 700, 550, 720, 580, 690, 500 -> >=600 keeps rows 1, 3, 5
    b = ae.legacy_policy_baseline(tiny_transactions, credit_score_cutoff=600, lgd=0.65)
    assert b["approved_count"] == 3
    assert b["approval_rate_pct"] == pytest.approx(50.0)
    # approved rows are exactly the non-defaulters here
    assert b["projected_fee_revenue"] == pytest.approx(10.0 + 30.0 + 50.0)
    assert b["projected_default_losses"] == pytest.approx(0.0)
    assert b["approved_default_rate"] == pytest.approx(0.0)


def test_legacy_policy_cutoff_is_monotonic_in_approval_rate(tiny_transactions):
    rates = [
        ae.legacy_policy_baseline(tiny_transactions, credit_score_cutoff=c, lgd=0.65)[
            "approval_rate_pct"
        ]
        for c in (500, 600, 700, 800)
    ]
    assert rates == sorted(rates, reverse=True)


# ------------------------------------------------------------- simulation

def test_simulation_rejects_misaligned_scores(tiny_transactions):
    """The single most dangerous failure mode in this codebase: scores that
    do not line up row-for-row with the transactions silently produce
    plausible but meaningless results."""
    with pytest.raises(ValueError, match="must align"):
        ae.simulate_thresholds(tiny_transactions, np.array([0.1, 0.2]))


def test_higher_threshold_never_approves_fewer(tiny_transactions, perfect_scores):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    counts = [p["approved_count"] for p in pts]
    assert counts == sorted(counts)


def test_loosest_threshold_reproduces_approve_all(tiny_transactions, perfect_scores):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[1.0], lgd=0.65
    )
    assert pts[0]["approved_count"] == 6
    assert pts[0]["projected_net_profit"] == pytest.approx(-570.0)


def test_perfect_ranking_screens_out_every_defaulter(tiny_transactions, perfect_scores):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05], lgd=0.65
    )
    p = pts[0]
    assert p["approved_count"] == 3
    assert p["approved_default_rate"] == pytest.approx(0.0)
    assert p["projected_default_losses"] == pytest.approx(0.0)
    assert p["projected_net_profit"] == pytest.approx(90.0)  # 10 + 30 + 50


def test_volume_retained_differs_from_approval_rate(tiny_transactions, perfect_scores):
    """Approving half the transactions is not the same as retaining half the
    volume — an important distinction when large tickets are the risky ones."""
    p = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05], lgd=0.65
    )[0]
    assert p["approval_rate_pct"] == pytest.approx(50.0)
    # approved principal = 100 + 300 + 500 = 900 of 2100
    assert p["volume_retained_pct"] == pytest.approx(42.86, abs=0.01)


def test_empty_threshold_points_are_skipped(tiny_transactions, perfect_scores):
    """A threshold that approves nothing produces no point rather than a
    divide-by-zero or a row of zeroes that would distort the chart."""
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.001], lgd=0.65
    )
    assert pts == []


# ------------------------------------------------------------------- grid

def test_grid_is_sorted_deduplicated_and_spans_the_range():
    grid = ae.default_threshold_grid(lo=0.005, hi=0.65)
    assert grid == sorted(grid)
    assert len(grid) == len(set(grid))
    assert min(grid) == pytest.approx(0.005)
    assert max(grid) < 0.65


def test_grid_is_finer_near_the_turning_point():
    """The original grid started at 0.05 in steps of 0.05, which made a
    boundary optimum indistinguishable from a located one."""
    grid = ae.default_threshold_grid()
    below = [t for t in grid if t < 0.05]
    assert len(below) >= 10


# -------------------------------------------------------------- strategies

def test_ladder_recommends_breakeven_over_the_profit_maximum(
    tiny_transactions, perfect_scores, legacy_stub
):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    ladder = ae.build_strategy_ladder(pts, legacy_stub, min_approval_rate_pct=40.0)
    assert ladder["recommended_strategy"] == "breakeven"
    assert ladder["strategies"]["breakeven"]["meets_volume_floor"] is True


def test_breakeven_never_approves_less_than_the_profit_maximum(
    tiny_transactions, perfect_scores, legacy_stub
):
    """Break-even maximises volume among viable points and the profit maximum
    is itself viable, so break-even can never be the smaller book."""
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    ladder = ae.build_strategy_ladder(pts, legacy_stub, min_approval_rate_pct=40.0)
    assert (
        ladder["strategies"]["breakeven"]["approval_rate_pct"]
        >= ladder["strategies"]["unconstrained_max"]["approval_rate_pct"]
    )


def test_shippability_follows_the_approval_rate_not_the_rule(
    tiny_transactions, perfect_scores, legacy_stub
):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    ladder = ae.build_strategy_ladder(pts, legacy_stub, min_approval_rate_pct=90.0)
    for s in ladder["strategies"].values():
        assert s["meets_volume_floor"] == (s["approval_rate_pct"] >= 90.0)


def test_breakeven_strategy_is_never_loss_making(
    tiny_transactions, perfect_scores, legacy_stub
):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    ladder = ae.build_strategy_ladder(pts, legacy_stub)
    assert ladder["strategies"]["breakeven"]["projected_net_profit"] >= 0


def test_unconstrained_optimum_is_the_global_maximum(
    tiny_transactions, perfect_scores, legacy_stub
):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    ladder = ae.build_strategy_ladder(pts, legacy_stub)
    best = max(p["projected_net_profit"] for p in pts)
    assert ladder["strategies"]["unconstrained_max"]["projected_net_profit"] == best


def test_constrained_optimum_respects_the_volume_floor(
    tiny_transactions, perfect_scores, legacy_stub
):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    ladder = ae.build_strategy_ladder(pts, legacy_stub, min_approval_rate_pct=90.0)
    assert ladder["strategies"]["constrained_max"]["approval_rate_pct"] >= 90.0


def test_boundary_optimum_is_detected_and_caveated(tiny_transactions, legacy_stub):
    """If the best point sits on the edge of the grid, the ladder must say
    so rather than presenting it as a located optimum."""
    scores = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
    clean = tiny_transactions.assign(is_default=0)  # profit rises monotonically
    pts = ae.simulate_thresholds(clean, scores, thresholds=[0.02, 0.04, 0.07], lgd=0.65)
    ladder = ae.build_strategy_ladder(pts, legacy_stub)
    assert ladder["boundary_optimum"] is True
    assert any("edge of the search grid" in c for c in ladder["caveats"])


def test_no_profitable_threshold_yields_no_recommendation(
    tiny_transactions, legacy_stub
):
    """When the book cannot be made profitable by declining alone, the
    product must say that, not silently recommend the least-bad option."""
    all_default = tiny_transactions.assign(is_default=1)
    scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    pts = ae.simulate_thresholds(all_default, scores, thresholds=[0.35, 0.7], lgd=0.65)
    ladder = ae.build_strategy_ladder(pts, legacy_stub)
    assert ladder["recommended_strategy"] is None
    assert ladder["recommended_threshold"] is None
    assert any("pricing" in c for c in ladder["caveats"])


def test_every_strategy_carries_its_caveats(
    tiny_transactions, perfect_scores, legacy_stub
):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    ladder = ae.build_strategy_ladder(pts, legacy_stub)
    assert any("synthetic" in c for c in ladder["caveats"])
    assert any("backtest" in c for c in ladder["caveats"])
    assert any("loss-given-default" in c for c in ladder["caveats"])


def test_profit_vs_legacy_is_computed_against_the_supplied_baseline(
    tiny_transactions, perfect_scores, legacy_stub
):
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05], lgd=0.65
    )
    ladder = ae.build_strategy_ladder(pts, legacy_stub)
    s = ladder["strategies"]["unconstrained_max"]
    assert s["profit_vs_legacy"] == pytest.approx(
        s["projected_net_profit"] - legacy_stub["projected_net_profit"]
    )


# ------------------------------------------------------------ edge / invalid

def test_empty_simulation_returns_no_recommendation(legacy_stub):
    ladder = ae.build_strategy_ladder([], legacy_stub)
    assert ladder["recommended_strategy"] is None
    assert ladder["strategies"] == {}


def test_zero_volume_portfolio_does_not_divide_by_zero():
    empty = pd.DataFrame({
        "transaction_id": [], "customer_id": [], "merchant_category": [],
        "transaction_amount": [], "fee_revenue": [], "num_installments": [],
        "is_default": [], "credit_score": [],
    })
    customers = pd.DataFrame({"customer_id": []})
    m = ae.portfolio_metrics(customers, empty, lgd=0.65)
    assert m["profit_margin_pct"] == 0.0
    assert m["total_transactions"] == 0


def test_threshold_at_approval_rate_picks_the_nearest_point():
    pts = [
        {"approval_rate_pct": 30.0, "approval_threshold": 0.05},
        {"approval_rate_pct": 70.0, "approval_threshold": 0.10},
        {"approval_rate_pct": 95.0, "approval_threshold": 0.30},
    ]
    assert ae.threshold_at_approval_rate(pts, 72.0)["approval_threshold"] == 0.10
    assert ae.threshold_at_approval_rate(pts, 10.0)["approval_threshold"] == 0.05
    assert ae.threshold_at_approval_rate([], 50.0) is None


def test_segments_partition_the_customer_base(tiny_customers, tiny_transactions):
    merged = tiny_transactions.merge(
        tiny_customers[["customer_id", "income"]], on="customer_id", how="left"
    )
    agg = ae.segment_customers(merged)
    summary = ae.summarize_segments(agg)
    assert sum(s["customer_count"] for s in summary) == len(agg)


def test_profit_floor_rises_to_legacy_when_legacy_is_already_profitable(
    tiny_transactions, perfect_scores
):
    """If today's policy already earns money, a strategy that merely reaches
    zero is a step backwards. The break-even floor must rise to match it."""
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    profitable_legacy = {"approval_rate_pct": 80.0, "projected_net_profit": 50.0}
    ladder = ae.build_strategy_ladder(pts, profitable_legacy)
    be = ladder["strategies"]["breakeven"]
    assert be["projected_net_profit"] >= 50.0
    assert be["profit_vs_legacy"] >= 0
    assert "current profit" in be["strategy_label"]


def test_recommendation_never_loses_money_against_the_baseline(
    tiny_transactions, perfect_scores
):
    for legacy_profit in (-1000.0, -1.0, 0.0, 25.0, 80.0):
        legacy = {"approval_rate_pct": 80.0, "projected_net_profit": legacy_profit}
        pts = ae.simulate_thresholds(
            tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
        )
        ladder = ae.build_strategy_ladder(pts, legacy)
        if ladder["recommended_strategy"] is not None:
            rec = ladder["strategies"][ladder["recommended_strategy"]]
            assert rec["profit_vs_legacy"] >= 0, (
                f"recommended a strategy worse than baseline at "
                f"legacy profit {legacy_profit}"
            )


def test_volume_floor_infeasibility_is_reported(tiny_transactions, perfect_scores,
                                                legacy_stub):
    """When the volume floor and the profit floor cannot both be met, the
    ladder must say so rather than quietly recommending a losing strategy."""
    pts = ae.simulate_thresholds(
        tiny_transactions, perfect_scores, thresholds=[0.05, 0.5, 0.99], lgd=0.65
    )
    feasible = ae.build_strategy_ladder(pts, legacy_stub, min_approval_rate_pct=40.0)
    infeasible = ae.build_strategy_ladder(pts, legacy_stub, min_approval_rate_pct=99.0)
    assert feasible["volume_floor_feasible"] is True
    assert infeasible["volume_floor_feasible"] is False


def test_unknown_env_keys_do_not_break_settings(tmp_path, monkeypatch):
    """A typo or stale key in .env must not crash the app at import time.

    Regression: an .env.example shipped with API_HOST/API_PORT — neither of
    which is a Settings field — and pydantic's default extra="forbid" turned
    that into a ValidationError before any error handler existed to explain it.
    """
    from app.config import Settings

    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("TOTALLY_MADE_UP_KEY", "x")

    s = Settings()
    assert s.loss_given_default == 0.65
    assert s.n_transactions == 42000


def test_economic_assumptions_are_overridable_from_env(monkeypatch):
    """The assumptions must actually be configurable, not just look it."""
    from app.config import Settings

    monkeypatch.setenv("LOSS_GIVEN_DEFAULT", "0.45")
    monkeypatch.setenv("MIN_APPROVAL_RATE_PCT", "60")
    monkeypatch.setenv("LEGACY_CREDIT_SCORE_CUTOFF", "640")

    s = Settings()
    assert s.loss_given_default == 0.45
    assert s.min_approval_rate_pct == 60
    assert s.legacy_credit_score_cutoff == 640
