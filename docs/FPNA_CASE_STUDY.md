# BNPL FP&A and profitability intelligence case study

## 1. Business problem

The original platform answered a risk-policy question: which transactions should a BNPL lender approve to improve contribution after credit losses? It did not answer the broader finance question: after revenue recognition, credit losses, and operating expenses, what is the monthly operating outlook and which planning levers matter most?

The extension preserves the original underwriting analysis and adds a distinct FP&A layer. This distinction prevents the established contribution-profit metric from being mislabeled as operating profit.

## 2. Baseline financial performance

The seeded synthetic source contains 5,000 customers and 42,000 transactions totaling $14.47M. Gross merchant fee revenue is $597,654. At 65% LGD, approve-all credit losses are $1,020,268 and contribution after credit loss is -$422,614.

The legacy credit-score policy approves 78.28% of applications and produces a projected $141,629 loss before operating expenses. The existing risk-adjusted recommendation produces $7,588 of contribution, a projected $149,217 improvement, at a 10.75 percentage-point approval reduction. These are backtest outputs on synthetic transactions, not realized savings.

## 3. Analytical approach

The FP&A layer follows the existing Python service architecture:

```text
Synthetic customers + transactions
        ↓
Legacy-policy simulated actuals
        ↓
Monthly management P&L
        ↓
Budget variance + 12-month forecast + scenarios + sensitivity
        ↓
DuckDB governed views and reconciliation
        ↓
FastAPI endpoints and React executive dashboard
```

All calculations have one Python owner. SQL views materialize the same results for reporting and are tested back to the Python totals.

## 4. Forecasting methodology

The base forecast starts after the final source month. The last three complete synthetic months establish the run-rate for originations, transactions, and active customers. Annual growth assumptions compound monthly. Flat seasonality is deliberate because one synthetic year cannot support seasonal inference.

No held-out month is used to predict itself. A rolling three-month benchmark on the final three complete source months produces 2.39% volume MAPE and 2.62% revenue MAPE.

## 5. Management P&L results

The base 12-month forecast produces:

- $15.37M origination volume.
- $11.53M approved volume.
- $476,085 merchant fee revenue.
- $479,544 expected credit losses.
- $713,124 operating expenses.
- -$716,582 operating profit.
- -150.5% operating margin.

The loss is not hidden by transaction volume: only merchant fees are recognized as revenue.

## 6. Budget variance findings

The simulated budget uses the first three complete historical months for calibration and evaluates the next eight complete months. Simulated actual operating profit is $101,955 below plan. The default/LGD component contributes $98,285 of unfavorable variance. Volume, fee-rate, loss-volume, and operating-cost components reconcile to total operating-profit variance within $0.02 rounding.

## 7. Scenario comparison

Downside, base, and upside forecasts use the same calculation chain with independent assumptions. Operating profit ranges from -$1.08M downside to -$463K upside. None reaches break-even, showing that policy selection cannot compensate for the modeled operating-cost base and credit economics by itself.

## 8. Key profitability drivers

Default rate and LGD tie as the largest tested sensitivities at approximately $47,954 of annual operating-profit impact for a ±10% shock. Merchant fee rate follows at $47,609. The ranking directs finance attention toward measured recoveries, underwriting-loss performance, and merchant pricing.

## 9. Recommended decisions

1. Preserve the $149K policy result as a contribution-profit claim, not operating profit.
2. Obtain recovery and cost data before using the model as a real company plan.
3. Evaluate risk-based pricing and installment-term policies alongside approval thresholds.
4. Use the governed DuckDB views for repeatable reporting and KPI lineage.
5. Set a commercial loss or margin target before selecting a forecast scenario.

## 10. Important limitations

- Synthetic data and simulated operating expenses.
- Assumed, unmeasured LGD.
- One year of history and no inferred seasonality.
- No funding cost, taxes, collections timing, or balance-sheet model.
- Scenario default rate is configured independently from approval policy.
- Validation measures a stable synthetic series, not real-world forecast performance.

## Reproduction

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/test_financials.py tests/test_fpna.py -q
python -c "from app.services.financial_reporting import build_reporting_snapshot; print(build_reporting_snapshot()['reconciliation'])"
uvicorn app.main:app --port 8000

cd ../frontend
npm ci
npm run build
npm run dev
```
