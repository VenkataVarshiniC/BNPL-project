"""DuckDB financial reporting model and reusable SQL views."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from app.config import settings
from app.data.loader import get_customers, get_transactions
from app.services.financial_engine import build_fpna_package


VIEW_NAMES = [
    "vw_monthly_financial_summary",
    "vw_merchant_category_profitability",
    "vw_credit_loss_reporting",
    "vw_opex_summary",
    "vw_budget_variance_report",
    "vw_forecast_vs_actual",
    "vw_scenario_summary",
    "vw_kpi_lineage",
]


class FinancialReportingStore:
    """Small semantic reporting layer backed by DuckDB.

    Tables are materialized from the same Python package used by the API. SQL
    views are presentation and reporting contracts; reconciliation confirms
    that no value changes while crossing the Python/SQL boundary.
    """

    def __init__(self, database: str | Path = ":memory:"):
        self.connection = duckdb.connect(str(database))

    def close(self) -> None:
        self.connection.close()

    def build(
        self,
        customers: pd.DataFrame | None = None,
        transactions: pd.DataFrame | None = None,
        package: dict | None = None,
    ) -> dict:
        customers = get_customers() if customers is None else customers
        transactions = get_transactions() if transactions is None else transactions
        package = build_fpna_package(customers, transactions) if package is None else package

        tx = transactions.merge(
            customers[["customer_id", "credit_score", "employment_status", "region"]],
            on="customer_id",
            how="left",
            validate="many_to_one",
        ).copy()
        tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
        tx["month"] = tx["transaction_date"].dt.to_period("M").dt.to_timestamp()
        tx["fee_rate"] = tx["fee_revenue"] / tx["transaction_amount"]

        actuals = pd.DataFrame(package["actuals"])
        forecast_frames = []
        for scenario, rows in package["scenarios"]["monthly"].items():
            frame = pd.DataFrame(rows)
            frame["scenario"] = scenario
            forecast_frames.append(frame)
        forecasts = pd.concat(forecast_frames, ignore_index=True)
        budget = pd.DataFrame(package["budget_vs_actual"]["monthly"])
        holdout = pd.DataFrame(package["validation"]["rows"])
        scenarios = pd.DataFrame(package["scenarios"]["comparison"])
        scenarios = scenarios.drop(columns=["assumptions"])
        kpi_lineage = pd.DataFrame([
            {"kpi": "Origination volume", "definition": "Gross requested transaction amount before approval", "source": "fact_transactions.transaction_amount", "calculation": "SUM(transaction_amount)"},
            {"kpi": "Approved volume", "definition": "Origination volume passing the applicable approval policy", "source": "fact_monthly_actuals / fact_forecast", "calculation": "SUM(approved_volume)"},
            {"kpi": "Merchant fee revenue", "definition": "Recognized merchant fee on approved volume", "source": "fee_revenue or approved_volume x merchant_fee_rate", "calculation": "SUM(merchant_fee_revenue)"},
            {"kpi": "Credit losses", "definition": "Defaulted approved principal adjusted for LGD", "source": "is_default, transaction_amount, loss_given_default", "calculation": "SUM(defaulted principal x LGD)"},
            {"kpi": "Operating profit", "definition": "Merchant fee revenue less credit losses and operating expenses", "source": "management P&L", "calculation": "revenue - credit_losses - operating_expenses"},
            {"kpi": "Operating margin", "definition": "Operating profit as a share of merchant fee revenue", "source": "management P&L", "calculation": "operating_profit / merchant_fee_revenue"},
        ])
        base = package["assumptions"]["base"]
        assumption_frame = pd.DataFrame([{
            "legacy_credit_score_cutoff": settings.legacy_credit_score_cutoff,
            "loss_given_default": base["loss_given_default"],
        }])

        inputs = {
            "tx_input": tx,
            "actual_input": actuals,
            "forecast_input": forecasts,
            "budget_input": budget,
            "holdout_input": holdout,
            "scenario_input": scenarios,
            "kpi_input": kpi_lineage,
            "assumption_input": assumption_frame,
        }
        for name, frame in inputs.items():
            self.connection.register(name, frame)

        ddl = """
        CREATE OR REPLACE TABLE fact_transactions AS SELECT * FROM tx_input;
        CREATE OR REPLACE TABLE fact_monthly_actuals AS SELECT * FROM actual_input;
        CREATE OR REPLACE TABLE fact_forecast AS SELECT * FROM forecast_input;
        CREATE OR REPLACE TABLE fact_budget_variance AS SELECT * FROM budget_input;
        CREATE OR REPLACE TABLE fact_holdout_validation AS SELECT * FROM holdout_input;
        CREATE OR REPLACE TABLE fact_scenario_summary AS SELECT * FROM scenario_input;
        CREATE OR REPLACE TABLE dim_kpi_lineage AS SELECT * FROM kpi_input;
        CREATE OR REPLACE TABLE dim_financial_assumptions AS SELECT * FROM assumption_input;

        CREATE OR REPLACE VIEW vw_monthly_financial_summary AS
        SELECT month, status, scenario, origination_volume, approved_volume,
               merchant_fee_revenue, credit_losses, operating_expenses,
               operating_profit, operating_margin, approval_rate
        FROM fact_monthly_actuals ORDER BY month;

        CREATE OR REPLACE VIEW vw_merchant_category_profitability AS
        SELECT merchant_category,
               COUNT(*) AS transaction_count,
               SUM(transaction_amount) AS transaction_volume,
               SUM(fee_revenue) AS merchant_fee_revenue,
               SUM(CASE WHEN is_default = 1 THEN transaction_amount ELSE 0 END)
                   * ANY_VALUE(loss_given_default) AS credit_losses,
               SUM(fee_revenue) -
               SUM(CASE WHEN is_default = 1 THEN transaction_amount ELSE 0 END)
                   * ANY_VALUE(loss_given_default) AS contribution_profit
        FROM fact_transactions
        CROSS JOIN dim_financial_assumptions
        GROUP BY merchant_category;

        CREATE OR REPLACE VIEW vw_credit_loss_reporting AS
        SELECT month, approved_volume, default_rate, loss_given_default,
               credit_losses,
               credit_losses / NULLIF(approved_volume, 0) AS loss_rate_on_approved_volume
        FROM fact_monthly_actuals ORDER BY month;

        CREATE OR REPLACE VIEW vw_opex_summary AS
        SELECT month, processing_expense, customer_acquisition_expense,
               servicing_expense, technology_expense, other_operating_expense,
               operating_expenses
        FROM fact_monthly_actuals ORDER BY month;

        CREATE OR REPLACE VIEW vw_budget_variance_report AS
        SELECT * FROM fact_budget_variance ORDER BY month;

        CREATE OR REPLACE VIEW vw_forecast_vs_actual AS
        SELECT month, training_through, predicted_origination_volume,
               actual_origination_volume, volume_absolute_percentage_error,
               predicted_revenue, actual_revenue,
               revenue_absolute_percentage_error
        FROM fact_holdout_validation ORDER BY month;

        CREATE OR REPLACE VIEW vw_scenario_summary AS
        SELECT * FROM fact_scenario_summary ORDER BY scenario;

        CREATE OR REPLACE VIEW vw_kpi_lineage AS
        SELECT * FROM dim_kpi_lineage ORDER BY kpi;
        """
        self.connection.execute(ddl)
        return package

    def query_view(self, name: str) -> list[dict]:
        if name not in VIEW_NAMES:
            raise ValueError(f"unknown reporting view: {name}")
        frame = self.connection.execute(f"SELECT * FROM {name}").fetchdf()
        for col in frame.select_dtypes(include=["datetime64[ns]"]).columns:
            frame[col] = frame[col].dt.strftime("%Y-%m-%d")
        return frame.where(pd.notna(frame), None).to_dict(orient="records")

    def reconcile(self, package: dict) -> dict:
        sql_actual = self.connection.execute(
            """SELECT SUM(merchant_fee_revenue), SUM(credit_losses),
                      SUM(operating_expenses), SUM(operating_profit)
               FROM fact_monthly_actuals"""
        ).fetchone()
        py_actual = [
            sum(r[key] for r in package["actuals"])
            for key in ("merchant_fee_revenue", "credit_losses", "operating_expenses", "operating_profit")
        ]
        sql_forecast = self.connection.execute(
            """SELECT SUM(merchant_fee_revenue), SUM(credit_losses),
                      SUM(operating_expenses), SUM(operating_profit)
               FROM fact_forecast WHERE scenario = 'base'"""
        ).fetchone()
        annual = package["forecast"]["annual"]
        py_forecast = [
            annual[key]
            for key in ("merchant_fee_revenue", "credit_losses", "operating_expenses", "operating_profit")
        ]
        differences = [
            round(float(sql - py), 8)
            for sql, py in zip((*sql_actual, *sql_forecast), (*py_actual, *py_forecast))
        ]
        return {
            "status": "PASS" if max(abs(x) for x in differences) <= 0.05 else "FAIL",
            "tolerance": 0.05,
            "differences": differences,
            "max_absolute_difference": max(abs(x) for x in differences),
        }


def build_reporting_snapshot(database: str | Path = ":memory:") -> dict:
    store = FinancialReportingStore(database)
    try:
        package = store.build()
        return {
            "views": {name: store.query_view(name) for name in VIEW_NAMES},
            "reconciliation": store.reconcile(package),
        }
    finally:
        store.close()
