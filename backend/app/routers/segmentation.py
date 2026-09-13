from fastapi import APIRouter

from app.data.loader import get_merged
from app.models.schemas import SegmentationResponse
from app.services.analytics_engine import segment_customers, summarize_segments

router = APIRouter(prefix="/api/segmentation", tags=["Segmentation"])


@router.get("/customers", response_model=SegmentationResponse)
def get_customer_segments():
    """
    Endpoint 1 — Customer segmentation.
    Answers: who are our customer cohorts and how do they differ in
    behavior, spend, and risk?
    """
    merged = get_merged()
    agg = segment_customers(merged)
    segments = summarize_segments(agg)
    return SegmentationResponse(total_customers=len(agg), segments=segments)
