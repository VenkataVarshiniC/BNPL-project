# Stakeholder Register

> ## Authenticity notice
>
> **This is an independent portfolio project with no external stakeholders.** Nobody listed below was consulted, interviewed or informed. There were no stakeholder meetings, no steering group, no sign-offs.
>
> Every entry is a **target stakeholder** — a role reasoned about from the decisions it would own at a BNPL lender, used to structure requirements and communication design. The register exists to show how stakeholder analysis *would* be conducted and how it shaped the product, not to imply it was conducted.
>
> The single real participant is the contributor, listed last.

---

## Interest / influence grid

```
            HIGH INFLUENCE
                  │
   Finance Mgr    │    Executive
   Risk Analyst   │    Product Manager
   ───────────────┼──────────────────  HIGH INTEREST →
   Data Eng.      │    Merchant Partners
   Compliance     │    Customers
                  │
            LOW INFLUENCE
```

**Manage closely:** Executive, Product Manager
**Keep satisfied:** Finance Manager, Risk Analyst
**Keep informed:** Merchant Partners, Compliance
**Monitor:** Data Engineering, Customers

---

## Primary stakeholders — direct product users

### S1 · Executive (Target) — *Manage closely*

| | |
|---|---|
| **Role** | Owns the P&L and the approval decision |
| **Interest** | High — the loss is theirs to answer for |
| **Influence** | High — approves or rejects the policy change |
| **Information needed** | The size of the loss · what causes it · one recommendation · its projected impact · what it costs in approval volume · the risks and the one or two assumptions that could invalidate it |
| **Communication** | Executive Dashboard and Decision Summary. One screen, one recommendation, trade-off stated. No methodology unless asked. |
| **Design consequence** | The decision summary leads with the recommendation and the volume forgone **in the same sentence**. A recommendation with no stated cost reads as advocacy rather than analysis. |

### S2 · Product Manager (Target) — *Manage closely*

| | |
|---|---|
| **Role** | Owns the BNPL product line and roadmap |
| **Interest** | High — must sequence the change against growth targets |
| **Influence** | High — decides what gets built and when |
| **Information needed** | Multiple strategies on consistent metrics · the volume cost of each profit gain in percentage points · which options are shippable and which are theoretical · a like-for-like comparison isolating selection from volume reduction |
| **Communication** | Strategy Simulator and Scenario Comparison. Comparative, not prescriptive. |
| **Design consequence** | The product reports **four** strategies rather than one optimum, and marks the profit-maximising one as an upper bound rather than a recommendation. Reporting a single optimum would have hidden the decision this stakeholder exists to make. |

### S3 · Finance Manager (Target) — *Keep satisfied*

| | |
|---|---|
| **Role** | Owns the P&L forecast; defends numbers that reach a board pack |
| **Interest** | High — will be asked to stand behind any projection |
| **Influence** | Medium-high — can veto a number as unforecastable |
| **Information needed** | Every assumption stated numerically in one place · sensitivity on the assumptions that move the answer · revenue, loss and profit reported separately · an explicit statement of what is backtest and what is forecast |
| **Communication** | Assumptions panel, LGD sensitivity table, standing caveats on every response. |
| **Design consequence** | Assumptions were lifted out of the analytics code into configuration and returned with **every** API response, so a projection cannot be quoted without them. The LGD sensitivity table exists because this stakeholder's first question is "what if 65% is wrong?" |

### S4 · Risk Analyst (Target) — *Keep satisfied*

| | |
|---|---|
| **Role** | Owns portfolio credit quality; produces the underlying analysis |
| **Interest** | High — the analysis is their professional output |
| **Influence** | Medium — recommends, does not decide |
| **Information needed** | Loss attributed by category with default rate beside profitability · drill-down without re-querying · score distributions and approved-population risk as the threshold moves · reproducible, auditable calculations |
| **Communication** | Risk Analysis and Merchant Analysis screens; raw API access. |
| **Design consequence** | Category net profits are asserted in test to sum to the portfolio figure. This stakeholder's credibility depends on reconciliation, so it is enforced mechanically rather than checked by eye. |

---

## Secondary stakeholders — affected, not users

### S5 · Merchant Partners (Target) — *Keep informed*

| | |
|---|---|
| **Interest** | High — approval rate directly determines their conversion |
| **Influence** | Medium — can leave for a competitor with looser policy |
| **Information needed** | Advance notice of approval-rate changes and the rationale |
| **Design consequence** | **This stakeholder is the reason the volume floor exists.** A profit optimiser with no volume constraint recommended declining 63% of the book — a policy that maximises modelled profit while destroying the merchant relationships the business runs on. See [DEC-04](decision-log.md). |

### S6 · Compliance / Legal (Target) — *Keep informed*

| | |
|---|---|
| **Interest** | Medium — automated credit decisions carry ECOA/FCRA obligations |
| **Influence** | High if triggered — can block deployment outright |
| **Information needed** | Whether the system makes decisions or supports them · model explainability · adverse-action capability |
| **Design consequence** | Reinforces the decision-support boundary. The system has **no write path** to any approval system, and the risk endpoint returns advisory language rather than approve/decline instructions. Adverse-action reason codes are named as the first compliance gap in the [roadmap](roadmap.md), not quietly omitted. |

### S7 · Data Engineering (Target) — *Monitor*

| | |
|---|---|
| **Interest** | Medium — would own the data pipeline in production |
| **Influence** | Low at MVP stage |
| **Information needed** | Data contracts, refresh cadence, model retraining requirements |
| **Design consequence** | Data loading is isolated behind a cached loader module, so the synthetic CSV source could be replaced without touching the analytics layer. |

### S8 · End Customers (Target) — *Monitor*

| | |
|---|---|
| **Interest** | High individually — approval affects them directly |
| **Influence** | Low individually |
| **Information needed** | None from this system; they never interact with it |
| **Design consequence** | Named explicitly because tightening approvals declines real people. The recommended strategy is the **least** restrictive one that stops the loss, rather than the most profitable one, partly for this reason. A 63%-decline policy is not a neutral optimisation outcome. |

---

## Actual participant

### S9 · Project/Product Lead — *the sole real stakeholder*

| | |
|---|---|
| **Role** | Single contributor holding product, analysis and engineering responsibility simultaneously |
| **Interest / Influence** | Total — every decision was made by this person alone |
| **Information needed** | — |
| **Communication** | [Decision log](decision-log.md), recording each significant choice with its options and accepted trade-off, since there was no second party to challenge them |

---

## Communication plan

*How this product **would** be communicated. No communications were actually issued.*

| Stakeholder | Channel | Cadence | Content |
|---|---|---|---|
| Executive | Decision Summary | At decision points | Recommendation, impact, trade-off, risks |
| Product Manager | Scenario Comparison | Weekly during evaluation | Strategy options and volume implications |
| Finance Manager | Assumptions + sensitivity | On every projection | Assumption set, sensitivity range, backtest caveats |
| Risk Analyst | Risk Analysis + API | Continuous | Attribution detail, reproducible calculations |
| Merchant Partners | Out of system | Ahead of any policy change | Approval-rate impact and rationale |
| Compliance | Architecture + decision log | Before any deployment step | Decision-support boundary, explainability, adverse-action gap |

---

## How stakeholder analysis actually changed the product

Three concrete design decisions trace directly to this register, and each is recorded in the [decision log](decision-log.md):

1. **Four strategies instead of one optimum** — because the Product Manager owns a trade-off, and a single number would have made that decision invisible (S2).
2. **An approval-volume floor** — because Merchant Partners and Customers bear the cost of a profit-maximising policy that the P&L alone would never surface (S5, S8).
3. **Assumptions returned with every response** — because the Finance Manager cannot forecast against a number whose assumptions can be separated from it in transit (S3).

Stakeholder analysis that changes nothing is decoration. These three are the test of whether it was worth doing.
