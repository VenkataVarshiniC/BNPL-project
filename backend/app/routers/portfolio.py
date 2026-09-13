from fastapi import APIRouter

from app.data.loader import get_customers, get_transactions
from app.models.schemas import PortfolioMetrics
from app.services.analytics_engine import portfolio_metrics

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("/profitability", response_model=PortfolioMetrics)
def get_portfolio_profitability():
    """
    Endpoint 4 — Portfolio-level profitability.
    Answers: net of defaults, where is the business actually making
    money across the entire book?
    """
    customers = get_customers()
    transactions = get_transactions()
    return portfolio_metrics(customers, transactions)
