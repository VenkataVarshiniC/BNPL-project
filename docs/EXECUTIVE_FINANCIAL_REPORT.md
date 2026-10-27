# Executive financial report

## Decision summary

The existing risk-adjusted policy finding remains valid: on the synthetic backtest, moving from the legacy credit-score policy to the maximum-volume break-even policy improves modeled contribution after credit loss by **$149,217**, while reducing approval rate by **10.75 percentage points**.

The management P&L adds the missing operating-cost view. Under base planning assumptions, the next 12 months produce **$15.37M of originations**, **$476,085 of merchant fee revenue**, **$479,544 of credit losses**, and **$713,124 of operating expenses**, resulting in a **$716,582 operating loss** and a **-150.5% operating margin**.

This is the central finance conclusion: approval policy can improve credit contribution, but approval tightening alone does not create a profitable operating model. Fee economics, loss performance, and cost structure must improve together.

## Scenario comparison

| Scenario | Origination volume | Revenue | Credit losses | Operating expenses | Operating profit | Operating margin |
|---|---:|---:|---:|---:|---:|---:|
| Downside | $14.34M | $391,387 | $639,767 | $836,280 | -$1,084,661 | -277.1% |
| Base | $15.37M | $476,085 | $479,544 | $713,124 | -$716,582 | -150.5% |
| Upside | $15.91M | $560,059 | $350,037 | $673,206 | -$463,183 | -82.7% |

All scenarios remain loss-making after modeled operating expenses. The upside case narrows the loss by $253,399 against base but does not reach break-even.

## Budget variance

Across eight held-out complete months, simulated actual operating profit is **$101,955 below budget**. The main attribution is a **$98,285 unfavorable default/LGD variance**. Revenue is $3,418 below budget and modeled operating expenses are $2,800 above budget. The bridge reconciles within $0.02.

## Profitability drivers

Default rate and LGD are tied as the largest one-way sensitivities because credit loss is their product. A ±10% change in either moves annual operating profit by approximately **$47,954**. Merchant fee rate is next at **$47,609**. These are materially larger than the tested fixed-cost and processing-rate shocks.

## Recommendations

1. Keep the existing risk-adjusted policy recommendation as a contribution-margin decision, clearly separate from operating-profit claims.
2. Prioritize measured recovery data. LGD uncertainty is large enough to change both the underwriting recommendation and the forward P&L.
3. Test risk-based merchant pricing and installment-term controls. The current fee rate does not cover expected credit loss plus operating expense in any modeled scenario.
4. Establish a finance data contract for general-ledger operating expenses before using the management P&L for a real budget.
5. Use the DuckDB views as the governed reporting layer so dashboard, SQL, and Python consumers share KPI definitions.

## Limitations

All results are generated from synthetic data and explicit planning assumptions. No value represents realized savings, audited profit, or a production forecast.
