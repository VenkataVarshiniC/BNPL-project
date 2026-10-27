from functools import lru_cache

from fastapi import APIRouter

from app.data.loader import get_customers, get_transactions
from app.services.financial_engine import build_fpna_package
from app.services.financial_reporting import build_reporting_snapshot


router = APIRouter(prefix="/api/fpna", tags=["FP&A"])


@lru_cache(maxsize=1)
def _package() -> dict:
    return build_fpna_package(get_customers(), get_transactions())


@router.get("/overview")
def get_fpna_overview():
    """Management P&L, forecast, budget variance, scenarios, and validation."""
    return _package()


@router.get("/scenarios")
def get_fpna_scenarios():
    data = _package()
    return {
        "assumptions": data["assumptions"],
        "scenarios": data["scenarios"],
        "sensitivity": data["sensitivity"],
    }


@router.get("/sql-reporting")
def get_sql_reporting():
    """Reusable DuckDB views plus Python-to-SQL reconciliation evidence."""
    return build_reporting_snapshot()
