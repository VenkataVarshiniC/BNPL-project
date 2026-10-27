# Forecast validation

## Validation design

The forward forecast does not train on future outcomes. Validation uses a rolling three-month mean evaluated on the final three complete synthetic months. Each prediction uses only months earlier than the month being evaluated.

| Held-out month | Training through | Predicted volume | Simulated actual volume | Volume APE | Predicted revenue | Simulated actual revenue | Revenue APE |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-06 | 2026-05 | $1,198,069 | $1,189,721 | 0.70% | $38,757 | $38,305 | 1.18% |
| 2026-07 | 2026-06 | $1,193,078 | $1,249,146 | 4.49% | $38,651 | $40,525 | 4.63% |
| 2026-08 | 2026-07 | $1,221,180 | $1,245,836 | 1.98% | $39,556 | $40,381 | 2.04% |

Results:

- Origination volume MAPE: **2.39%**, or **97.61% accuracy** using `1 − MAPE`.
- Merchant fee revenue MAPE: **2.62%**, or **97.38% accuracy** using `1 − MAPE`.

These figures measure stability of a seeded synthetic series. They are not evidence of accuracy on a real BNPL portfolio.

## Financial reconciliation

- Monthly rows reconcile revenue less credit losses less five operating-expense categories to operating profit.
- Quarterly totals reconcile to the 12-month forecast within $0.05 rounding tolerance.
- The eight-month budget bridge has a cumulative rounding difference of **$0.02**.
- DuckDB and Python outputs reconcile with a maximum absolute difference of **$0.00** across actual and base-forecast revenue, credit losses, operating expenses, and operating profit.

## Coverage

Automated tests cover:

- Assumption bounds and invalid inputs.
- Monthly P&L identities.
- Revenue recognition on approved volume.
- Twelve-month chronology.
- Quarterly and annual reconciliation.
- Budget bridge reconciliation.
- Holdout date ordering to prevent forward leakage.
- Scenario consistency.
- Sensitivity ranking.
- DuckDB view population and Python/SQL reconciliation.

The complete backend suite passes: **57 tests** total, comprising the pre-existing financial and API error-contract coverage plus 10 new FP&A/SQL tests. In the restricted sandbox, threaded TestClient cases require an unrestricted local run; the final unrestricted verification completed in 6.41 seconds.

## Remaining validation work

- Backtest across multiple independent synthetic vintages.
- Add prediction intervals and parameter uncertainty.
- Replace assumed expenses with general-ledger actuals.
- Couple approval policy to forecast default rates using the full threshold curve.
- Validate DuckDB views against an external BI consumer.
