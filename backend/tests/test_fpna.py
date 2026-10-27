import pandas as pd
import pytest

from app.data.loader import get_customers, get_transactions
from app.services.financial_engine import (
    DEFAULT_SCENARIOS,
    PlanningAssumptions,
    build_budget_vs_actual,
    build_fpna_package,
    build_simulated_actuals,
    forecast_monthly,
    sensitivity_analysis,
    summarize_financials,
    validate_holdout_forecast,
)
from app.services.financial_reporting import FinancialReportingStore, VIEW_NAMES


@pytest.fixture(scope="module")
def actuals():
    return build_simulated_actuals(get_customers(), get_transactions())


@pytest.fixture(scope="module")
def package():
    return build_fpna_package(get_customers(), get_transactions())


def test_planning_assumptions_reject_invalid_rates():
    bad = PlanningAssumptions(**{
        **DEFAULT_SCENARIOS["base"].__dict__,
        "approval_rate": 1.1,
    })
    with pytest.raises(ValueError, match="approval_rate"):
        bad.validate()


def test_simulated_actual_pnl_reconciles(actuals):
    for row in actuals:
        assert row["net_revenue"] == pytest.approx(
            row["merchant_fee_revenue"] - row["credit_losses"], abs=0.02
        )
        assert row["operating_profit"] == pytest.approx(
            row["net_revenue"] - row["operating_expenses"], abs=0.02
        )


def test_forecast_has_twelve_chronological_months(actuals):
    rows = forecast_monthly(actuals, DEFAULT_SCENARIOS["base"])
    months = pd.to_datetime([r["month"] for r in rows])
    assert len(rows) == 12
    assert months.is_monotonic_increasing
    assert months.is_unique


def test_forecast_revenue_is_approved_volume_times_fee_rate(actuals):
    for row in forecast_monthly(actuals, DEFAULT_SCENARIOS["base"]):
        assert row["merchant_fee_revenue"] == pytest.approx(
            row["approved_volume"] * row["merchant_fee_rate"], abs=0.02
        )


def test_quarterly_and_annual_forecast_reconcile(actuals):
    rows = forecast_monthly(actuals, DEFAULT_SCENARIOS["base"])
    annual = summarize_financials(rows, "annual")[0]
    quarters = summarize_financials(rows, "quarterly")
    for key in ("merchant_fee_revenue", "credit_losses", "operating_expenses", "operating_profit"):
        assert sum(q[key] for q in quarters) == pytest.approx(annual[key], abs=0.05)


def test_budget_variance_bridge_reconciles(actuals):
    report = build_budget_vs_actual(actuals)
    assert report["monthly"]
    for row in report["monthly"]:
        assert row["operating_profit_variance"] == pytest.approx(
            row["bridge_total"], abs=0.05
        )
    assert report["total"]["operating_profit_variance"] == pytest.approx(
        report["total"]["bridge_total"], abs=0.05
    )


def test_holdout_validation_never_uses_future_month(actuals):
    result = validate_holdout_forecast(actuals)
    for row in result["rows"]:
        assert pd.Timestamp(row["training_through"]) < pd.Timestamp(row["month"])
    assert 0 <= result["volume_accuracy"] <= 1
    assert 0 <= result["revenue_accuracy"] <= 1


def test_sensitivity_is_sorted_and_contains_required_drivers(actuals):
    result = sensitivity_analysis(actuals)
    impacts = [row["max_absolute_impact"] for row in result]
    assert impacts == sorted(impacts, reverse=True)
    assert {"approval_rate", "merchant_fee_rate", "default_rate", "loss_given_default"}.issubset(
        {row["driver"] for row in result}
    )


def test_scenarios_are_independently_evaluated(package):
    comparison = {row["scenario"]: row for row in package["scenarios"]["comparison"]}
    assert set(comparison) == {"downside", "base", "upside"}
    assert comparison["downside"]["operating_profit"] < comparison["base"]["operating_profit"]
    assert comparison["base"]["operating_profit"] < comparison["upside"]["operating_profit"]


def test_duckdb_views_reconcile_to_python(package):
    store = FinancialReportingStore()
    try:
        store.build(get_customers(), get_transactions(), package)
        assert store.reconcile(package)["status"] == "PASS"
        for name in VIEW_NAMES:
            assert store.query_view(name)
    finally:
        store.close()
