from fastapi import APIRouter, HTTPException

from app.data.loader import get_customers
from app.models.schemas import RiskScoreRequest, RiskScoreResponse
from app.services.risk_model import score_single, risk_tier

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.post("/score", response_model=RiskScoreResponse)
def score_transaction_risk(payload: RiskScoreRequest):
    """
    Endpoint 3 — Default risk scoring.
    Answers: what's the probability a given customer defaults on a
    proposed transaction, and what should we do about it?
    """
    customers = get_customers()
    customer_row = customers[customers["customer_id"] == payload.customer_id]
    if customer_row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {payload.customer_id} not found")

    c = customer_row.iloc[0]

    probability = score_single(
        age=float(c["age"]),
        income=float(c["income"]),
        credit_score=float(c["credit_score"]),
        transaction_amount=payload.transaction_amount,
        num_installments=payload.num_installments,
        merchant_category=payload.merchant_category,
        employment_status=str(c["employment_status"]),
        region=str(c["region"]),
    )

    tier, action = risk_tier(probability)

    return RiskScoreResponse(
        customer_id=payload.customer_id,
        default_probability=round(probability, 4),
        risk_tier=tier,
        recommended_action=action,
    )
