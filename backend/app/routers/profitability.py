from fastapi import APIRouter

from app.data.loader import get_transactions
from app.models.schemas import ProfitabilityResponse
from app.services.analytics_engine import category_profitability

router = APIRouter(prefix="/api/profitability", tags=["Profitability"])


@router.get("/merchants", response_model=ProfitabilityResponse)
def get_merchant_category_profitability():
    """
    Endpoint 2 — Merchant/category profitability.
    Answers: which merchant categories generate margin vs. drag it down,
    net of estimated default losses?
    """
    transactions = get_transactions()
    categories = category_profitability(transactions)
    return ProfitabilityResponse(total_categories=len(categories), categories=categories)
