from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from app.data.loader import get_customers, get_transactions
from app.models.schemas import ExplainabilityResponse
from app.services.explainability import explain_row

router = APIRouter(prefix="/api/explainability", tags=["Explainability"])


@router.get("/{customer_id}", response_model=ExplainabilityResponse)
def explain_customer_risk(
    customer_id: str,
    transaction_amount: float | None = Query(None, gt=0),
    num_installments: int | None = Query(None, gt=0, le=24),
    merchant_category: str | None = Query(None),
):
    """
    Endpoint 6 — Explainability.
    Answers: why did the model flag this customer as high/low risk?
    Returns a SHAP feature-contribution breakdown for the prediction.
    If transaction params are omitted, uses the customer's historical
    average transaction as a representative example.
    """
    customers = get_customers()
    customer_row = customers[customers["customer_id"] == customer_id]
    if customer_row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    c = customer_row.iloc[0]

    if transaction_amount is None or num_installments is None or merchant_category is None:
        transactions = get_transactions()
        cust_txns = transactions[transactions["customer_id"] == customer_id]
        if cust_txns.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No transaction history for {customer_id}; provide transaction params explicitly.",
            )
        transaction_amount = transaction_amount or float(cust_txns["transaction_amount"].mean())
        num_installments = num_installments or int(cust_txns["num_installments"].mode()[0])
        merchant_category = merchant_category or cust_txns["merchant_category"].mode()[0]

    feature_row = pd.DataFrame([{
        "transaction_amount": transaction_amount,
        "num_installments": num_installments,
        "age": float(c["age"]),
        "income": float(c["income"]),
        "credit_score": float(c["credit_score"]),
        "merchant_category": merchant_category,
        "employment_status": str(c["employment_status"]),
        "region": str(c["region"]),
    }])

    result = explain_row(feature_row)

    return ExplainabilityResponse(
        customer_id=customer_id,
        default_probability=result["default_probability"],
        base_value=result["base_value"],
        top_contributions=result["top_contributions"],
    )
