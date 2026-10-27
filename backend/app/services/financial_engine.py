"""FP&A planning, management P&L, variance, and scenario calculations.

The source portfolio is synthetic.  Historical outputs in this module are
therefore labelled ``simulated_actual``: they are observed rows from the
synthetic transaction file evaluated under the documented legacy approval
policy, not realised company results.

All operating-cost values are explicit planning assumptions because the source
dataset contains no general-ledger or cost-centre data.  The existing
``analytics_engine`` remains the owner of the locked risk/profitability metrics.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Iterable

import numpy as np
import pandas as pd

from app.config import settings


@dataclass(frozen=True)
class PlanningAssumptions:
    scenario: str
    annual_transaction_growth: float
    annual_customer_growth: float
    approval_rate: float
    merchant_fee_rate: float
    default_rate: float
    loss_given_default: float
    processing_cost_rate: float
    acquisition_cost_per_customer: float
    servicing_cost_per_transaction: float
    technology_monthly: float
    other_opex_monthly: float
    seasonality: tuple[float, ...] = (1.0,) * 12

    def validate(self) -> None:
        rates = {
            "approval_rate": self.approval_rate,
            "merchant_fee_rate": self.merchant_fee_rate,
            "default_rate": self.default_rate,
            "loss_given_default": self.loss_given_default,
            "processing_cost_rate": self.processing_cost_rate,
        }
        for name, value in rates.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.annual_transaction_growth <= -1 or self.annual_customer_growth <= -1:
            raise ValueError("annual growth assumptions must be greater than -100%")
        if len(self.seasonality) != 12 or any(x <= 0 for x in self.seasonality):
            raise ValueError("seasonality must contain 12 positive monthly factors")
        if not np.isclose(sum(self.seasonality), 12.0, atol=1e-6):
            raise ValueError("seasonality factors must average 1.0")
        costs = (
            self.acquisition_cost_per_customer,
            self.servicing_cost_per_transaction,
            self.technology_monthly,
            self.other_opex_monthly,
        )
        if any(x < 0 for x in costs):
            raise ValueError("cost assumptions cannot be negative")


DEFAULT_SCENARIOS: dict[str, PlanningAssumptions] = {
    "downside": PlanningAssumptions(
        scenario="downside",
        annual_transaction_growth=-0.05,
        annual_customer_growth=-0.02,
        approval_rate=0.70,
        merchant_fee_rate=0.039,
        default_rate=0.085,
        loss_given_default=0.75,
        processing_cost_rate=0.009,
        acquisition_cost_per_customer=22.0,
        servicing_cost_per_transaction=0.90,
        technology_monthly=42_000.0,
        other_opex_monthly=18_000.0,
    ),
    "base": PlanningAssumptions(
        scenario="base",
        annual_transaction_growth=0.08,
        annual_customer_growth=0.06,
        approval_rate=0.75,
        merchant_fee_rate=0.0413,
        default_rate=0.064,
        loss_given_default=0.65,
        processing_cost_rate=0.0075,
        acquisition_cost_per_customer=18.0,
        servicing_cost_per_transaction=0.75,
        technology_monthly=35_000.0,
        other_opex_monthly=15_000.0,
    ),
    "upside": PlanningAssumptions(
        scenario="upside",
        annual_transaction_growth=0.15,
        annual_customer_growth=0.10,
        approval_rate=0.80,
        merchant_fee_rate=0.044,
        default_rate=0.050,
        loss_given_default=0.55,
        processing_cost_rate=0.0065,
        acquisition_cost_per_customer=16.0,
        servicing_cost_per_transaction=0.65,
        technology_monthly=33_000.0,
        other_opex_monthly=14_000.0,
    ),
}


MONEY_COLUMNS = [
    "origination_volume",
    "approved_volume",
    "merchant_fee_revenue",
    "credit_losses",
    "processing_expense",
    "customer_acquisition_expense",
    "servicing_expense",
    "technology_expense",
    "other_operating_expense",
    "operating_expenses",
    "net_revenue",
    "operating_profit",
]


def _monthly_rate(annual_rate: float) -> float:
    return (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0


def _round_record(record: dict) -> dict:
    for key in MONEY_COLUMNS:
        if key in record:
            record[key] = round(float(record[key]), 2)
    for key in (
        "approval_rate",
        "merchant_fee_rate",
        "default_rate",
        "loss_given_default",
        "operating_margin",
    ):
        if key in record:
            record[key] = round(float(record[key]), 6)
    return record


def _pnl_record(
    *,
    month: pd.Timestamp,
    status: str,
    scenario: str,
    origination_volume: float,
    transaction_count: int,
    active_customers: int,
    approved_volume: float,
    approved_transaction_count: int,
    merchant_fee_revenue: float,
    credit_losses: float,
    processing_expense: float,
    customer_acquisition_expense: float,
    servicing_expense: float,
    technology_expense: float,
    other_operating_expense: float,
    approval_rate: float,
    merchant_fee_rate: float,
    default_rate: float,
    loss_given_default: float,
) -> dict:
    operating_expenses = (
        processing_expense
        + customer_acquisition_expense
        + servicing_expense
        + technology_expense
        + other_operating_expense
    )
    net_revenue = merchant_fee_revenue - credit_losses
    operating_profit = net_revenue - operating_expenses
    return _round_record({
        "month": pd.Timestamp(month).strftime("%Y-%m-01"),
        "status": status,
        "scenario": scenario,
        "origination_volume": origination_volume,
        "transaction_count": int(transaction_count),
        "active_customers": int(active_customers),
        "approved_volume": approved_volume,
        "approved_transaction_count": int(approved_transaction_count),
        "approval_rate": approval_rate,
        "merchant_fee_rate": merchant_fee_rate,
        "default_rate": default_rate,
        "loss_given_default": loss_given_default,
        "merchant_fee_revenue": merchant_fee_revenue,
        "credit_losses": credit_losses,
        "net_revenue": net_revenue,
        "processing_expense": processing_expense,
        "customer_acquisition_expense": customer_acquisition_expense,
        "servicing_expense": servicing_expense,
        "technology_expense": technology_expense,
        "other_operating_expense": other_operating_expense,
        "operating_expenses": operating_expenses,
        "operating_profit": operating_profit,
        "operating_margin": operating_profit / merchant_fee_revenue
        if merchant_fee_revenue else 0.0,
    })


def build_simulated_actuals(
    customers: pd.DataFrame,
    transactions: pd.DataFrame,
    assumptions: PlanningAssumptions | None = None,
    credit_score_cutoff: int | None = None,
) -> list[dict]:
    """Monthly management P&L from observed synthetic rows.

    Transactions are treated as applications and evaluated under the legacy
    credit-score policy, matching the existing backtest convention.  Revenue
    and defaults come from the selected source rows.  Operating expenses are
    simulated from explicit planning assumptions because no expense ledger is
    present in the repository.
    """
    assumptions = assumptions or DEFAULT_SCENARIOS["base"]
    assumptions.validate()
    cutoff = settings.legacy_credit_score_cutoff if credit_score_cutoff is None else credit_score_cutoff

    tx = transactions.copy()
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
    tx["month"] = tx["transaction_date"].dt.to_period("M").dt.to_timestamp()
    merged = tx.merge(
        customers[["customer_id", "credit_score"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
    if merged["credit_score"].isna().any():
        raise ValueError("transactions contain customer IDs missing from customers")

    output: list[dict] = []
    previous_active = 0
    for month, all_rows in merged.groupby("month", sort=True):
        approved = all_rows[all_rows["credit_score"] >= cutoff]
        origination_volume = float(all_rows["transaction_amount"].sum())
        approved_volume = float(approved["transaction_amount"].sum())
        fee_revenue = float(approved["fee_revenue"].sum())
        credit_losses = float(
            approved.loc[approved["is_default"].eq(1), "transaction_amount"].sum()
            * assumptions.loss_given_default
        )
        active_customers = int(approved["customer_id"].nunique())
        acquired = max(active_customers - previous_active, 0) if output else 0
        previous_active = active_customers
        record = _pnl_record(
            month=month,
            status="simulated_actual",
            scenario="legacy_policy",
            origination_volume=origination_volume,
            transaction_count=len(all_rows),
            active_customers=active_customers,
            approved_volume=approved_volume,
            approved_transaction_count=len(approved),
            merchant_fee_revenue=fee_revenue,
            credit_losses=credit_losses,
            processing_expense=approved_volume * assumptions.processing_cost_rate,
            customer_acquisition_expense=acquired * assumptions.acquisition_cost_per_customer,
            servicing_expense=len(approved) * assumptions.servicing_cost_per_transaction,
            technology_expense=assumptions.technology_monthly,
            other_operating_expense=assumptions.other_opex_monthly,
            approval_rate=len(approved) / len(all_rows) if len(all_rows) else 0.0,
            merchant_fee_rate=fee_revenue / approved_volume if approved_volume else 0.0,
            default_rate=float(approved["is_default"].mean()) if len(approved) else 0.0,
            loss_given_default=assumptions.loss_given_default,
        )
        record["is_partial_month"] = bool(
            all_rows["transaction_date"].dt.day.nunique() < 25
        )
        output.append(record)
    return output


def _calibration(actuals: list[dict]) -> dict:
    complete = [row for row in actuals if not row.get("is_partial_month")]
    source = complete[-3:] if len(complete) >= 3 else actuals[-3:]
    if not source:
        raise ValueError("at least one historical month is required")
    return {
        "origination_volume": float(np.mean([r["origination_volume"] for r in source])),
        "transaction_count": float(np.mean([r["transaction_count"] for r in source])),
        "active_customers": float(np.mean([r["active_customers"] for r in source])),
        "last_month": pd.Timestamp(actuals[-1]["month"]),
        "source_months": [r["month"] for r in source],
    }


def forecast_monthly(
    actuals: list[dict],
    assumptions: PlanningAssumptions,
    periods: int = 12,
    start_month: pd.Timestamp | None = None,
) -> list[dict]:
    assumptions.validate()
    if periods <= 0:
        raise ValueError("periods must be positive")
    base = _calibration(actuals)
    start = (
        pd.Timestamp(start_month).to_period("M").to_timestamp()
        if start_month is not None
        else base["last_month"] + pd.offsets.MonthBegin(1)
    )
    tx_growth = _monthly_rate(assumptions.annual_transaction_growth)
    customer_growth = _monthly_rate(assumptions.annual_customer_growth)
    prior_customers = base["active_customers"]
    rows: list[dict] = []
    for idx in range(periods):
        month = start + pd.offsets.MonthBegin(idx)
        seasonal = assumptions.seasonality[idx % 12]
        volume = base["origination_volume"] * ((1 + tx_growth) ** (idx + 1)) * seasonal
        transaction_count = max(
            1,
            round(base["transaction_count"] * ((1 + tx_growth) ** (idx + 1)) * seasonal),
        )
        active_customers = max(
            1, round(base["active_customers"] * ((1 + customer_growth) ** (idx + 1)))
        )
        acquired = max(active_customers - round(prior_customers), 0)
        prior_customers = active_customers
        approved_volume = volume * assumptions.approval_rate
        approved_count = round(transaction_count * assumptions.approval_rate)
        fee_revenue = approved_volume * assumptions.merchant_fee_rate
        credit_losses = (
            approved_volume * assumptions.default_rate * assumptions.loss_given_default
        )
        rows.append(_pnl_record(
            month=month,
            status="forecast",
            scenario=assumptions.scenario,
            origination_volume=volume,
            transaction_count=transaction_count,
            active_customers=active_customers,
            approved_volume=approved_volume,
            approved_transaction_count=approved_count,
            merchant_fee_revenue=fee_revenue,
            credit_losses=credit_losses,
            processing_expense=approved_volume * assumptions.processing_cost_rate,
            customer_acquisition_expense=acquired * assumptions.acquisition_cost_per_customer,
            servicing_expense=approved_count * assumptions.servicing_cost_per_transaction,
            technology_expense=assumptions.technology_monthly,
            other_operating_expense=assumptions.other_opex_monthly,
            approval_rate=assumptions.approval_rate,
            merchant_fee_rate=assumptions.merchant_fee_rate,
            default_rate=assumptions.default_rate,
            loss_given_default=assumptions.loss_given_default,
        ))
    return rows


def summarize_financials(rows: Iterable[dict], period: str = "annual") -> list[dict]:
    frame = pd.DataFrame(list(rows))
    if frame.empty:
        return []
    frame["month"] = pd.to_datetime(frame["month"])
    if period == "quarterly":
        frame["summary_period"] = frame["month"].dt.to_period("Q").astype(str)
    elif period == "calendar_year":
        frame["summary_period"] = frame["month"].dt.year.astype(str)
    elif period == "annual":
        frame["summary_period"] = "12-month forecast"
    else:
        raise ValueError("period must be quarterly, calendar_year, or annual")

    output = []
    for label, group in frame.groupby("summary_period", sort=True):
        result = {"period": str(label), "months": int(len(group))}
        for col in MONEY_COLUMNS:
            result[col] = round(float(group[col].sum()), 2)
        result["transaction_count"] = int(group["transaction_count"].sum())
        result["approved_transaction_count"] = int(group["approved_transaction_count"].sum())
        result["active_customers_end"] = int(group.sort_values("month").iloc[-1]["active_customers"])
        result["approval_rate"] = round(
            result["approved_transaction_count"] / result["transaction_count"], 6
        ) if result["transaction_count"] else 0.0
        result["operating_margin"] = round(
            result["operating_profit"] / result["merchant_fee_revenue"], 6
        ) if result["merchant_fee_revenue"] else 0.0
        output.append(result)
    return output


def build_budget_vs_actual(
    actuals: list[dict],
    assumptions: PlanningAssumptions | None = None,
    materiality_dollars: float = 5_000.0,
    materiality_pct: float = 0.05,
) -> dict:
    """Create a simulated budget and an exact operating-profit bridge.

    The first three complete historical months establish the planning run-rate;
    subsequent complete months are held out as simulated actuals.  No future
    month is used to set an earlier month's budget.
    """
    assumptions = assumptions or DEFAULT_SCENARIOS["base"]
    assumptions.validate()
    complete = [r for r in actuals if not r.get("is_partial_month")]
    if len(complete) < 5:
        raise ValueError("at least five complete months are required for budget analysis")
    calibration, evaluation = complete[:3], complete[3:]
    base_volume = float(np.mean([r["origination_volume"] for r in calibration]))
    base_count = float(np.mean([r["transaction_count"] for r in calibration]))
    base_customers = float(np.mean([r["active_customers"] for r in calibration]))
    tx_growth = _monthly_rate(assumptions.annual_transaction_growth)
    customer_growth = _monthly_rate(assumptions.annual_customer_growth)
    prior_customers = base_customers
    rows = []
    for idx, actual in enumerate(evaluation, start=1):
        volume = base_volume * ((1 + tx_growth) ** idx)
        tx_count = max(1, round(base_count * ((1 + tx_growth) ** idx)) )
        active_customers = max(1, round(base_customers * ((1 + customer_growth) ** idx)))
        acquired = max(active_customers - round(prior_customers), 0)
        prior_customers = active_customers
        approved_volume = volume * assumptions.approval_rate
        approved_count = round(tx_count * assumptions.approval_rate)
        budget = _pnl_record(
            month=pd.Timestamp(actual["month"]),
            status="budget",
            scenario="base_budget",
            origination_volume=volume,
            transaction_count=tx_count,
            active_customers=active_customers,
            approved_volume=approved_volume,
            approved_transaction_count=approved_count,
            merchant_fee_revenue=approved_volume * assumptions.merchant_fee_rate,
            credit_losses=approved_volume * assumptions.default_rate * assumptions.loss_given_default,
            processing_expense=approved_volume * assumptions.processing_cost_rate,
            customer_acquisition_expense=acquired * assumptions.acquisition_cost_per_customer,
            servicing_expense=approved_count * assumptions.servicing_cost_per_transaction,
            technology_expense=assumptions.technology_monthly,
            other_operating_expense=assumptions.other_opex_monthly,
            approval_rate=assumptions.approval_rate,
            merchant_fee_rate=assumptions.merchant_fee_rate,
            default_rate=assumptions.default_rate,
            loss_given_default=assumptions.loss_given_default,
        )
        actual_fee_rate = (
            actual["merchant_fee_revenue"] / actual["approved_volume"]
            if actual["approved_volume"] else 0.0
        )
        actual_loss_rate = (
            actual["credit_losses"] / actual["approved_volume"]
            if actual["approved_volume"] else 0.0
        )
        budget_loss_rate = assumptions.default_rate * assumptions.loss_given_default
        volume_variance = (
            actual["approved_volume"] - budget["approved_volume"]
        ) * assumptions.merchant_fee_rate
        fee_rate_variance = actual["approved_volume"] * (
            actual_fee_rate - assumptions.merchant_fee_rate
        )
        loss_volume_variance = (
            actual["approved_volume"] - budget["approved_volume"]
        ) * budget_loss_rate
        default_loss_variance = actual["approved_volume"] * (
            actual_loss_rate - budget_loss_rate
        )
        operating_cost_variance = actual["operating_expenses"] - budget["operating_expenses"]
        revenue_variance = actual["merchant_fee_revenue"] - budget["merchant_fee_revenue"]
        credit_loss_variance = actual["credit_losses"] - budget["credit_losses"]
        profit_variance = actual["operating_profit"] - budget["operating_profit"]
        bridge = (
            volume_variance + fee_rate_variance
            - loss_volume_variance - default_loss_variance
            - operating_cost_variance
        )
        threshold = max(materiality_dollars, abs(budget["operating_profit"]) * materiality_pct)
        rows.append({
            "month": actual["month"],
            "budget_revenue": budget["merchant_fee_revenue"],
            "actual_revenue": actual["merchant_fee_revenue"],
            "revenue_variance": round(revenue_variance, 2),
            "revenue_variance_pct": round(revenue_variance / budget["merchant_fee_revenue"], 6)
            if budget["merchant_fee_revenue"] else None,
            "budget_expenses": budget["operating_expenses"],
            "actual_expenses": actual["operating_expenses"],
            "expense_variance": round(operating_cost_variance, 2),
            "budget_operating_profit": budget["operating_profit"],
            "actual_operating_profit": actual["operating_profit"],
            "operating_profit_variance": round(profit_variance, 2),
            "operating_profit_variance_pct": round(profit_variance / abs(budget["operating_profit"]), 6)
            if budget["operating_profit"] else None,
            "favorable_unfavorable": "Favorable" if profit_variance >= 0 else "Unfavorable",
            "material": abs(profit_variance) >= threshold,
            "materiality_threshold": round(threshold, 2),
            "volume_variance": round(volume_variance, 2),
            "fee_rate_variance": round(fee_rate_variance, 2),
            "loss_volume_variance": round(loss_volume_variance, 2),
            "default_loss_variance": round(default_loss_variance, 2),
            "operating_cost_variance": round(operating_cost_variance, 2),
            "credit_loss_variance": round(credit_loss_variance, 2),
            "bridge_total": round(bridge, 2),
            "reconciliation_difference": round(profit_variance - bridge, 2),
        })

    totals = {
        key: round(sum(float(r[key]) for r in rows), 2)
        for key in (
            "budget_revenue", "actual_revenue", "revenue_variance",
            "budget_expenses", "actual_expenses", "expense_variance",
            "budget_operating_profit", "actual_operating_profit",
            "operating_profit_variance", "volume_variance", "fee_rate_variance",
            "loss_volume_variance", "default_loss_variance",
            "operating_cost_variance", "credit_loss_variance", "bridge_total",
            "reconciliation_difference",
        )
    }
    totals["favorable_unfavorable"] = (
        "Favorable" if totals["operating_profit_variance"] >= 0 else "Unfavorable"
    )
    totals["months"] = len(rows)
    return {
        "method": "First three complete synthetic months set the budget run-rate; later complete months are held out as simulated actuals.",
        "calibration_months": [r["month"] for r in calibration],
        "monthly": rows,
        "total": totals,
    }


def validate_holdout_forecast(actuals: list[dict], holdout_months: int = 3) -> dict:
    complete = [r for r in actuals if not r.get("is_partial_month")]
    if len(complete) < holdout_months + 3:
        raise ValueError("not enough complete months for holdout validation")
    start = len(complete) - holdout_months
    rows = []
    for idx in range(start, len(complete)):
        train = complete[max(0, idx - 3):idx]
        actual = complete[idx]
        volume_pred = float(np.mean([r["origination_volume"] for r in train]))
        revenue_pred = float(np.mean([r["merchant_fee_revenue"] for r in train]))
        volume_error = abs(actual["origination_volume"] - volume_pred) / actual["origination_volume"]
        revenue_error = abs(actual["merchant_fee_revenue"] - revenue_pred) / actual["merchant_fee_revenue"]
        rows.append({
            "month": actual["month"],
            "training_through": train[-1]["month"],
            "predicted_origination_volume": round(volume_pred, 2),
            "actual_origination_volume": actual["origination_volume"],
            "volume_absolute_percentage_error": round(volume_error, 6),
            "predicted_revenue": round(revenue_pred, 2),
            "actual_revenue": actual["merchant_fee_revenue"],
            "revenue_absolute_percentage_error": round(revenue_error, 6),
        })
    volume_mape = float(np.mean([r["volume_absolute_percentage_error"] for r in rows]))
    revenue_mape = float(np.mean([r["revenue_absolute_percentage_error"] for r in rows]))
    return {
        "method": "Rolling three-month mean evaluated on the final three complete synthetic months; each prediction uses only prior months.",
        "rows": rows,
        "volume_mape": round(volume_mape, 6),
        "volume_accuracy": round(max(0.0, 1.0 - volume_mape), 6),
        "revenue_mape": round(revenue_mape, 6),
        "revenue_accuracy": round(max(0.0, 1.0 - revenue_mape), 6),
    }


def scenario_comparison(actuals: list[dict]) -> dict:
    forecasts = {
        name: forecast_monthly(actuals, assumptions)
        for name, assumptions in DEFAULT_SCENARIOS.items()
    }
    comparison = []
    for name, rows in forecasts.items():
        total = summarize_financials(rows, "annual")[0]
        comparison.append({
            "scenario": name,
            "transaction_volume": total["origination_volume"],
            "approved_volume": total["approved_volume"],
            "revenue": total["merchant_fee_revenue"],
            "credit_losses": total["credit_losses"],
            "operating_expenses": total["operating_expenses"],
            "operating_profit": total["operating_profit"],
            "operating_margin": total["operating_margin"],
            "approval_rate": total["approval_rate"],
            "assumptions": asdict(DEFAULT_SCENARIOS[name]),
        })
    return {"monthly": forecasts, "comparison": comparison}


def sensitivity_analysis(actuals: list[dict], shock: float = 0.10) -> list[dict]:
    if shock <= 0 or shock >= 1:
        raise ValueError("shock must be between 0 and 1")
    base = DEFAULT_SCENARIOS["base"]
    base_profit = summarize_financials(forecast_monthly(actuals, base), "annual")[0]["operating_profit"]
    drivers = [
        "annual_transaction_growth", "approval_rate", "merchant_fee_rate",
        "default_rate", "loss_given_default", "processing_cost_rate",
        "technology_monthly", "other_opex_monthly",
    ]
    output = []
    for driver in drivers:
        current = getattr(base, driver)
        low_value = current * (1 - shock)
        high_value = current * (1 + shock)
        if driver in {"annual_transaction_growth"}:
            low_value = current - shock
            high_value = current + shock
        if driver in {"approval_rate", "merchant_fee_rate", "default_rate", "loss_given_default", "processing_cost_rate"}:
            low_value = max(0.0, low_value)
            high_value = min(1.0, high_value)
        low = replace(base, scenario=f"base_{driver}_low", **{driver: low_value})
        high = replace(base, scenario=f"base_{driver}_high", **{driver: high_value})
        low_profit = summarize_financials(forecast_monthly(actuals, low), "annual")[0]["operating_profit"]
        high_profit = summarize_financials(forecast_monthly(actuals, high), "annual")[0]["operating_profit"]
        output.append({
            "driver": driver,
            "base_value": current,
            "low_value": low_value,
            "high_value": high_value,
            "base_operating_profit": base_profit,
            "low_operating_profit": low_profit,
            "high_operating_profit": high_profit,
            "low_impact": round(low_profit - base_profit, 2),
            "high_impact": round(high_profit - base_profit, 2),
            "max_absolute_impact": round(max(abs(low_profit - base_profit), abs(high_profit - base_profit)), 2),
        })
    return sorted(output, key=lambda x: x["max_absolute_impact"], reverse=True)


def build_fpna_package(customers: pd.DataFrame, transactions: pd.DataFrame) -> dict:
    actuals = build_simulated_actuals(customers, transactions)
    base_forecast = forecast_monthly(actuals, DEFAULT_SCENARIOS["base"])
    scenarios = scenario_comparison(actuals)
    sensitivity = sensitivity_analysis(actuals)
    annual = summarize_financials(base_forecast, "annual")[0]
    return {
        "labels": {
            "historical": "simulated actuals from the synthetic portfolio",
            "forecast": "forward planning forecast",
            "budget": "simulated budget",
            "currency": "USD",
        },
        "accounting_simplifications": [
            "Merchant fees are recognized when an approved transaction originates.",
            "Credit losses equal approved principal multiplied by observed or assumed default rate and LGD; no timing or collections curve is modeled.",
            "Processing, acquisition, servicing, technology, and other operating expenses are planning assumptions because the source repository has no general ledger.",
            "Funding costs, interest income, taxes, depreciation, interchange, chargebacks, and working-capital effects are outside scope.",
        ],
        "assumptions": {name: asdict(value) for name, value in DEFAULT_SCENARIOS.items()},
        "actuals": actuals,
        "forecast": {
            "monthly": base_forecast,
            "quarterly": summarize_financials(base_forecast, "quarterly"),
            "calendar_year": summarize_financials(base_forecast, "calendar_year"),
            "annual": annual,
        },
        "budget_vs_actual": build_budget_vs_actual(actuals),
        "scenarios": scenarios,
        "sensitivity": sensitivity,
        "validation": validate_holdout_forecast(actuals),
        "executive_summary": {
            "base_operating_profit": annual["operating_profit"],
            "base_operating_margin": annual["operating_margin"],
            "highest_impact_driver": sensitivity[0]["driver"],
            "historical_months": len(actuals),
            "forecast_months": len(base_forecast),
        },
    }
