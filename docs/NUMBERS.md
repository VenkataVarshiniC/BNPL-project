# Locked Number Set

**Single source of truth.** Every figure in the README, PRD, portfolio case study, dashboard and résumé must come from this file. If a number is not here, it does not go in a document.

**Generated:** 12 Sep 2026
**Dataset:** synthetic, seed 42, 5,000 customers / 42,000 transactions
**Model:** GradientBoostingClassifier, 150 estimators, depth 3, lr 0.08
**Environment:** scikit-learn 1.5.1 · numpy 1.26.4 · pandas 2.2.2 (pinned versions)
**Reconciled:** independently reproduced on a second environment (scikit-learn 1.8.0 / numpy 2.4.4 / pandas 3.0.2) — see cross-version note below

> **Cross-version reproducibility — verified.** Every figure below was produced on the pinned versions and independently reproduced on scikit-learn 1.8.0 / numpy 2.4.4 / pandas 3.0.2. All portfolio, baseline and category figures matched **exactly**. Across the four strategies, a single value differed: the unconstrained profit maximum came out $1.17 higher on 1.8.0 ($61,375.09 vs $61,373.92), a rounding-level difference in gradient-boosting internals. **The recommended headline figure of $149,217 was identical on both.**
>
> This is a stronger reproducibility claim than a single-environment run, and it is the evidence behind NFR-01.

---

## Model quality

| Metric | Value |
|---|---|
| Holdout AUC (20% split) | **0.7043** |
| Out-of-fold AUC (5-fold) | **0.7076** |
| Training rows | 33,600 |
| Holdout rows | 8,400 |
| Out-of-fold scored rows | 42,000 |

Out-of-fold AUC is what the strategy simulation runs on. It is marginally *higher* than the holdout AUC, which is normal — each fold model trains on 80% of the data and the OOF estimate averages five of them.

---

## Portfolio (gross, before any approval policy)

| Metric | Value |
|---|---|
| Customers | 5,000 |
| Transactions | 42,000 |
| Merchant categories | 10 |
| Gross transaction volume | $14,471,392 |
| Fee revenue | $597,654 |
| Default losses @ 65% LGD | $1,020,268 |
| **Net profit** | **−$422,614** |
| Overall default rate | 9.59% |
| Margin on volume | −2.92% |

---

## Policy comparators

| Policy | Approval rate | Approved default rate | Net profit |
|---|---:|---:|---:|
| Approve all *(reference only, not a real policy)* | 100.00% | 9.59% | **−$422,614** |
| **Legacy: credit score ≥ 600** *(the baseline)* | 78.28% | 7.07% | **−$141,629** |

The legacy policy is the honest baseline. It approves 32,877 of 42,000 transactions on credit score alone, ignoring installment count, merchant category and employment status — all of which carry default signal. That omission is the **risk-adjustment gap** the project investigates.

Approve-all is retained only to isolate gross book economics. **It must never be used as the comparator for an improvement claim.**

---

## Strategy ladder — risk-adjusted approval

All four use out-of-fold model scores. Improvement is measured against the **legacy** baseline.

| Strategy | Threshold | Approval rate | Δ approval | Approved default rate | Net profit | **Improvement** |
|---|---:|---:|---:|---:|---:|---:|
| Risk-adjusted at current volume | 0.130 | 78.04% | −0.24pp | 6.61% | −$60,956 | **+$80,673** |
| **Maximum volume at break-even** ⭐ | **0.105** | **67.53%** | **−10.75pp** | **5.73%** | **+$7,588** | **+$149,217** |
| Most profitable above 75% approval | 0.1225 | 75.31% | −2.97pp | 6.40% | −$41,115 | +$100,514 |
| Maximum profit (any volume) | 0.0575 | 36.77% | −41.51pp | 3.87% | +$61,374 | +$203,003 |

⭐ **Recommended.** Highest approval rate at which the book stops losing money.

**Boundary optimum: FALSE.** The grid extends down to 0.005 in 0.0025 steps; the profit maximum at 0.0575 is a genuine interior optimum, not a grid artifact. *(The original 0.05-step grid could not have established this.)*

**Volume floor feasible: FALSE.** The configured 75% approval floor and profitability cannot both be satisfied. The most profitable threshold holding 75% approval still loses $41,115. This conflict is the central finding, not a bug.

---

## The headline figure — choose one, use it everywhere

| Framing | Baseline | Strategy | Figure | Defensibility |
|---|---|---|---:|---|
| **A — Risk adjustment at constant volume** | Legacy −$141,629 | 78.04% approval | **+$80,673** | **Strongest.** No volume given up; the entire gain comes from better selection. Hardest to attack. |
| **B — Recommended policy** ⭐ | Legacy −$141,629 | Break-even, 67.53% | **+$149,217** | **Recommended headline.** A real decision with a stated trade-off: 10.75pp of approvals for a swing from loss to profit. |
| C — Theoretical maximum | Legacy −$141,629 | 36.77% approval | +$203,003 | Upper bound only. Approves a third of the book; label as unshippable. |
| D — Against approve-all | Approve-all −$422,614 | 36.77% approval | +$483,988 | **The previous framing.** Not false, but the baseline is a straw man and the approval rate is unshippable. Avoid as a headline. |

The previously submitted **$470K** corresponds to framing D. It is not inflated relative to that framing — D actually computes to $483,988 — but D is the weakest of the four and should be retired as the headline.

### Recommended résumé phrasing (framing B)

> Built a BNPL risk-and-profitability decision platform on a synthetic 42,000-transaction portfolio; identified a risk-adjustment gap in credit-score-only underwriting and modelled a scoring policy projected to move the book from a $142K loss to break-even, a **$149K projected improvement** under stated assumptions, at a 10.75pp reduction in approval rate.

Never: "saved", "delivered", "generated", "in production", "for a client".
Always: "projected", "modelled", "synthetic", "under stated assumptions".

---

## Merchant-category profitability (gross, approve-all)

| Category | Txns | Volume | Fee revenue | Default losses | Net profit | Margin | Default rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Beauty & Wellness | 4,149 | $370,938 | $22,256 | $19,647 | **+$2,609** | 0.70% | 8.34% |
| Health & Fitness | 4,111 | $617,181 | $27,773 | $26,713 | **+$1,061** | 0.17% | 6.59% |
| Groceries | 4,330 | $259,342 | $7,780 | $8,312 | −$531 | −0.20% | 4.97% |
| Fashion & Apparel | 4,129 | $539,867 | $29,693 | $34,094 | −$4,401 | −0.82% | 9.88% |
| Sporting Goods | 4,195 | $756,253 | $37,813 | $46,977 | −$9,164 | −1.21% | 9.75% |
| Jewelry & Accessories | 4,194 | $1,475,857 | $95,931 | $123,448 | −$27,517 | −1.86% | 13.02% |
| Electronics | 4,168 | $1,750,013 | $78,751 | $137,536 | −$58,785 | −3.36% | 11.95% |
| Education | 4,236 | $2,094,022 | $52,351 | $111,366 | −$59,015 | −2.82% | 8.29% |
| Home & Furniture | 4,271 | $2,805,852 | $112,234 | $202,100 | −$89,866 | −3.20% | 11.05% |
| **Travel** | 4,217 | $3,802,069 | $133,072 | $310,076 | **−$177,003** | −4.66% | 12.14% |

Category net profits sum to the portfolio net profit (asserted in `test_category_profits_sum_to_portfolio_profit`).

**Loss drivers, in order:** Of the **$426,283** lost across the eight loss-making categories, Travel alone accounts for **41.5%**, and Travel, Home & Furniture, Education and Electronics together account for **90.2%**. *(Denominator is the sum of loss-making categories, which is what the product reports. Against the portfolio net figure of −$422,614 — smaller, because the two profitable categories offset it — the same shares are 41.9% and 91.0%.)* The pattern is large average ticket combined with an elevated default rate — Travel carries the highest average ticket ($902) *and* the second-highest default rate, while its 3.5% fee rate is the lowest of the ten. Only two categories are profitable, and both are small-ticket, low-risk.

---

## Sensitivity to the LGD assumption

Recommended (break-even) strategy, recomputed at each LGD:

| LGD | Legacy baseline | Rec. threshold | Approval rate | Net profit | Improvement |
|---:|---:|---:|---:|---:|---:|
| 45% | +$46,049 | 0.160 | 86.17% | +$50,383 | +$4,334 |
| 55% | −$47,790 | 0.135 | 79.69% | +$3,597 | +$51,387 |
| **65%** *(base case)* | **−$141,629** | **0.105** | **67.53%** | **+$7,588** | **+$149,217** |
| 75% | −$235,469 | 0.085 | 57.23% | +$5,469 | +$240,937 |
| 85% | −$329,308 | 0.070 | 47.35% | +$5,410 | +$334,718 |

**The headline figure is highly sensitive to LGD.** At 45% recovery-adjusted severity the book is already profitable and the whole problem dissolves; at 85% it needs a 47% approval rate to survive. LGD is an assumption, not a measurement, and this table must appear anywhere the improvement figure appears.

---

## Standing caveats — reproduce verbatim

1. Projected under modelled assumptions on a **synthetic** portfolio — not a measured, realised or audited result.
2. Approval decisions use **out-of-fold** model scores; losses on the approved subset use actual outcomes. This is a **backtest**, not a forward forecast.
3. All loss figures are conditional on a **65% loss-given-default** assumption (see sensitivity above).
4. The 75% volume floor cannot be met profitably — the most profitable threshold meeting it still loses $41,115.

---

## Reproduce

```bash
cd backend
pip install -r requirements.txt
python -m app.data.generate_synthetic_data   # 5,000 / 42,000, seed 42
python -m app.ml.train_model                 # model + 5-fold OOF scores
python -m pytest -q                          # 40 tests
uvicorn app.main:app --port 8000
curl "http://localhost:8000/api/optimization/thresholds" | python -m json.tool
```
