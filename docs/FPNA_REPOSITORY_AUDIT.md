# FP&A repository audit

## Baseline reviewed

- Branch audited: `main` at `f8bb8b8`.
- Architecture: FastAPI services and routers, pandas/scikit-learn analytics, React/Vite frontend, pytest financial tests, and seeded synthetic CSV/model artifacts.
- Source portfolio: 5,000 unique customers and 42,000 unique transactions; no orphan customer keys or duplicate transaction IDs.
- Date coverage: 2025-09-14 through 2026-09-13, with partial boundary months.

## Reconciled financial evidence

| Measure | Verified value |
|---|---:|
| Gross transaction volume | $14,471,392.45 |
| Merchant fee revenue | $597,654.19 |
| Defaulted principal | $1,569,643.03 |
| Credit losses at 65% LGD | $1,020,267.97 |
| Approve-all contribution after credit loss | -$422,613.78 |
| Legacy-policy approval rate | 78.28% |
| Legacy-policy contribution | -$141,629.28 |
| Recommended risk-adjusted contribution | $7,587.84 |
| Improvement versus legacy | $149,217.12 |
| Approval-rate change | -10.75 percentage points |

Category transaction counts reconcile exactly to 42,000. Category contribution reconciles within one cent of portfolio contribution because displayed category values are rounded individually.

## Existing controls worth preserving

- Financial logic is centralized in `analytics_engine.py` rather than duplicated in the frontend.
- Merchant fee revenue is separated from gross volume.
- Credit loss uses an explicit LGD assumption.
- Policy simulations use five-fold out-of-fold predictions, avoiding in-sample leakage.
- The strategy ladder distinguishes risk selection at constant approval, break-even, constrained profit, and the unconstrained upper bound.
- Documentation consistently labels the portfolio synthetic and the results projected.

## Gaps identified before implementation

- No forward monthly forecast or quarterly/annual rollup.
- No categorized management P&L or operating expenses.
- No budget, materiality, or root-cause variance bridge.
- No independent FP&A scenarios or ranked sensitivity analysis.
- No SQL semantic layer, KPI lineage, or Python/SQL reconciliation.
- No executive finance dashboard.
- No forecast-validation evidence or FP&A resume evidence.

## Baseline verification

- Existing financial calculation suite: 40 passed.
- Existing frontend production build: passed; Vite reported a bundle-size warning.
- npm audit at install time: 12 findings (6 moderate, 6 high), not automatically modified because `npm audit fix --force` could introduce breaking changes.
- Complete backend suite after implementation: 57 passed. Threaded TestClient cases required an unrestricted local run because the restricted sandbox blocks their worker-thread/loopback path.

## Implemented extension plan

1. Preserve the locked risk calculations and add a separate FP&A service.
2. Label historical synthetic rows, simulated expenses, forecasts, and budgets distinctly.
3. Use one Python calculation chain for management P&L, budget variance, scenarios, and sensitivities.
4. Materialize governed DuckDB reporting tables and reusable views from those outputs.
5. Reconcile SQL totals to Python before exposing them through FastAPI and React.
6. Document accounting simplifications, validation boundaries, and resume language guardrails.
