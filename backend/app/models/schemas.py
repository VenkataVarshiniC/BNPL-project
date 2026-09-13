from pydantic import BaseModel, Field
from typing import Optional


# ---------- Segmentation ----------

class CustomerSegment(BaseModel):
    segment_name: str
    customer_count: int
    avg_income: float
    avg_credit_score: float
    avg_transaction_count: float
    avg_total_spend: float
    default_rate: float


class SegmentationResponse(BaseModel):
    total_customers: int
    segments: list[CustomerSegment]


# ---------- Merchant / category profitability ----------

class MerchantCategoryProfitability(BaseModel):
    merchant_category: str
    transaction_count: int
    total_volume: float
    total_fee_revenue: float
    total_default_losses: float
    net_profit: float
    profit_margin_pct: float
    default_rate: float


class ProfitabilityResponse(BaseModel):
    total_categories: int
    categories: list[MerchantCategoryProfitability]


# ---------- Risk scoring ----------

class RiskScoreRequest(BaseModel):
    customer_id: str
    transaction_amount: float = Field(gt=0)
    num_installments: int = Field(gt=0, le=24)
    merchant_category: str


class RiskScoreResponse(BaseModel):
    customer_id: str
    default_probability: float
    risk_tier: str
    recommended_action: str


# ---------- Portfolio profitability ----------

class PortfolioMetrics(BaseModel):
    total_customers: int
    total_transactions: int
    total_volume: float
    total_fee_revenue: float
    total_default_losses: float
    net_profit: float
    overall_default_rate: float
    profit_margin_pct: float
    loss_given_default: float


# ---------- Policy baselines ----------

class PolicyBaseline(BaseModel):
    policy_name: str
    policy_type: str
    description: str
    approval_rate_pct: float
    approved_count: int
    approved_default_rate: float
    projected_fee_revenue: float
    projected_default_losses: float
    projected_net_profit: float
    credit_score_cutoff: Optional[int] = None


# ---------- Risk-adjusted optimization ----------

class ThresholdSimulationPoint(BaseModel):
    approval_threshold: float
    approval_rate_pct: float
    volume_retained_pct: float
    approved_count: int
    approved_default_rate: float
    projected_net_profit: float
    projected_fee_revenue: float
    projected_default_losses: float


class Strategy(ThresholdSimulationPoint):
    """A named point on the profit/volume trade-off."""
    strategy_key: str
    strategy_label: str
    meets_volume_floor: bool
    rationale: str
    profit_vs_legacy: float
    approval_rate_change_pp: float


class OptimizationResponse(BaseModel):
    simulated_points: list[ThresholdSimulationPoint]

    # Four named strategies spanning the trade-off, keyed by strategy_key.
    # `recommended_strategy` names the one the product actually recommends;
    # the unconstrained profit maximum is retained as a labelled upper bound.
    strategies: dict[str, Strategy]
    recommended_strategy: Optional[str] = None
    recommended_threshold: Optional[float] = None
    recommended_reason: str

    min_approval_rate_pct: float
    boundary_optimum: bool
    volume_floor_feasible: bool
    profit_floor: float
    caveats: list[str]

    legacy_baseline: PolicyBaseline
    approve_all_baseline: PolicyBaseline

    assumptions: dict


# ---------- Explainability ----------

class FeatureContribution(BaseModel):
    feature: str
    value: float
    shap_contribution: float


class ExplainabilityResponse(BaseModel):
    customer_id: str
    default_probability: float
    base_value: float
    top_contributions: list[FeatureContribution]
