# Project Charter — LedgerGuard BNPL Risk & Profitability Decision Platform

| | |
|---|---|
| **Project** | BNPL Risk & Profitability Decision Platform |
| **Type** | Independent portfolio project — individual contributor |
| **Charter date** | 12 September 2026 |
| **Status** | MVP delivered |
| **Document owner** | Project/Product Lead (single contributor — see [RACI](raci.md)) |

> **Scope of this document.** This is an independent portfolio project. It has no commissioning client, no external stakeholders and no production deployment. Stakeholders and personas named here are **target roles**, defined to structure product decisions — not people who were consulted. All financial figures are **projections on a synthetic dataset**, not realised results. See [NUMBERS.md](NUMBERS.md).

---

## 1. Problem

A BNPL lender earns a merchant fee on every transaction and absorbs the unrecovered principal when a customer defaults. Profitability therefore depends entirely on whether the approval policy separates customers who will repay from those who will not.

On a modelled 42,000-transaction portfolio, a conventional credit-score-only underwriting policy (approve at credit score ≥ 600) approves 78.28% of applications and produces a **projected net loss of $141,629** against $468,326 of fee revenue.

The loss is not evenly distributed. Two of ten merchant categories are profitable. **Travel alone accounts for 41.5% of the $426,283 lost across the eight loss-making categories**, and four categories account for 90.2% of it. The pattern is consistent: large average ticket combined with elevated default rate, priced at a fee rate that does not compensate for the risk.

The underlying cause is a **risk-adjustment gap**. Credit score is a single, general-purpose signal. It ignores installment count, merchant category and employment status — each of which carries independent default signal in this portfolio. The policy is not mispriced so much as under-informed.

## 2. Objective

Build a decision-support platform that lets business stakeholders understand where BNPL profitability is being lost, simulate alternative approval strategies against explicit assumptions, compare those strategies on a like-for-like basis, and reach a documented recommendation with its trade-offs stated.

**The platform supports a lending decision. It does not make one.** No transaction is approved, declined or priced by this system.

## 3. Success criteria

| # | Criterion | Measure | Status |
|---|---|---|---|
| SC1 | The loss and its drivers are legible without analyst assistance | A non-technical user identifies the loss-making categories in under 30 seconds | Met |
| SC2 | Alternative strategies can be simulated against changeable assumptions | LGD, approval floor and baseline cutoff are all user-adjustable and recompute end to end | Met |
| SC3 | Every reported figure is reproducible from source | `generate → train → pytest → API` reproduces every number in NUMBERS.md | Met |
| SC4 | Financial logic is tested independently of its outputs | Test suite asserts hand-computed values; no test pins a headline figure | Met — 40 tests |
| SC5 | A recommendation exists with its trade-off quantified | Recommended strategy names the profit gained and the approval volume forgone | Met |
| SC6 | Modelled results are never presented as realised | Every projection carries its caveats in the API response and the UI | Met |

## 4. Scope

### In scope
Portfolio profitability analysis · merchant-category loss attribution · RFM-style customer segmentation · default-risk scoring with SHAP explanation · approval-strategy simulation · multi-strategy comparison · executive decision summary · assumption sensitivity · test coverage of financial logic · UAT.

### Out of scope
Automated or real-time lending decisions · customer-facing BNPL application · real financial transactions or real customer data · authentication and multi-tenancy · production deployment and SLAs · regulatory compliance (ECOA/FCRA adverse-action logic) · fully autonomous AI decision-making · collections and recovery workflow · risk-based pricing engine *(identified as the natural next lever — see [roadmap](roadmap.md))*.

## 5. Deliverables

**Product** — FastAPI analytics backend (7 endpoints), React decision dashboard (executive summary, risk analysis, merchant analysis, strategy simulator, scenario comparison, decision summary), reproducible synthetic data generator, gradient-boosting risk model with out-of-fold evaluation.

**Project artefacts** — this charter · [PRD](PRD.md) · [personas](personas.md) · [user stories](user-stories.md) · [product backlog](product-backlog.md) · [roadmap](roadmap.md) · [stakeholder register](stakeholder-register.md) · [RACI](raci.md) · [risk register](risk-register.md) · [RAID log](raid-log.md) · [decision log](decision-log.md) · [UAT plan](uat-plan.md) · [retrospective](retrospective.md) · [architecture](architecture.md) · [portfolio case study](portfolio-case-study.md) · [locked number set](NUMBERS.md).

## 6. Stakeholders

Four **target personas** shape requirements: Risk Analyst, Product Manager, Finance Manager, Executive. Defined from the decisions each role would need to make, not from interviews. Full detail in the [stakeholder register](stakeholder-register.md) and [personas](personas.md).

## 7. Constraints

| C1 | Three calendar days of build time, single contributor. Forces MVP discipline: five product features and fifteen artefacts, no deployment, no auth. |
|---|---|
| **C2** | **No real BNPL data is lawfully obtainable for a portfolio project.** All data is synthetic and generated locally. This bounds every claim the project can make. |
| **C3** | No access to real BNPL practitioners. Personas and stakeholders are reasoned constructs and are labelled as such. |
| **C4** | Loss-given-default cannot be measured, only assumed. Every profit figure is conditional on it. |
| **C5** | The existing codebase must be preserved and extended, not rebuilt. |

## 8. Assumptions

| A1 | Merchant fee revenue is earned at transaction time and is not clawed back on a later default. |
|---|---|
| **A2** | **65% of principal is unrecovered on default (LGD).** An assumption, not a measurement. Sensitivity is published across 45–85%. |
| **A3** | The synthetic generator's default process — driven by credit score, income, installment count, category and employment — is a defensible caricature of BNPL default behaviour, not a calibrated model of it. |
| **A4** | Approval decisions are evaluated as a backtest: policy applied on out-of-fold predicted probability, losses realised from actual outcomes. |
| **A5** | Declining a transaction forgoes its fee revenue entirely — no substitution to a different product or term. |
| **A6** | The credit-score-≥-600 legacy policy is a reasonable stand-in for conventional underwriting. |

## 9. Key risks

Full register with scores, mitigations and owners: [risk-register.md](risk-register.md). The four that shaped the build:

- **Synthetic data cannot support real-world claims** — mitigated by labelling every figure as projected and synthetic at the API layer, so the caveat cannot be lost in presentation.
- **Optimisation produces a commercially invalid answer** — materialised. The unconstrained optimum declines 63% of the book. Mitigated by replacing single-optimum reporting with a four-strategy ladder and an explicit volume floor. See [DEC-03](decision-log.md).
- **In-sample scoring inflates projected profit** — materialised. Mitigated by five-fold out-of-fold scoring; corrected the projected optimum from $70,006 to $61,374.
- **Assumption sensitivity understated** — mitigated by publishing the LGD sensitivity table alongside every headline figure.

## 10. Timeline

**Actual development: three days (10–12 September 2026).** The [roadmap](roadmap.md) presents an eight-week *proposed* product delivery structure, and the [backlog](product-backlog.md) a five-sprint *proposed* agile structure. Neither describes how this project was actually built, and both are labelled accordingly.

| Day | Focus | Outcome |
|---|---|---|
| 1 | Audit · analytical correction · PM foundation | Three analytical defects fixed; numbers locked; charter, PRD, personas, stories, backlog, roadmap, stakeholders, RACI |
| 2 | Product build | Executive dashboard, risk analysis, strategy simulator, scenario comparison, decision summary |
| 3 | Governance · validation · narrative | Risk register, RAID, decision log, UAT execution, retrospective, architecture, README, case study |

## 11. Authority

Single contributor holding Project/Product Lead, Data/Analytics and Engineering roles simultaneously. All decisions are recorded in the [decision log](decision-log.md) with the options considered and the trade-off accepted. No approval gates exist, and none are claimed.
