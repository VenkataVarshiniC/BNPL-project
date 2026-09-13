# Product Requirements Document

**Product** LedgerGuard — BNPL Risk & Profitability Decision Platform
**Version** 1.0 · 12 September 2026 · **Status** MVP delivered
**Author** Project/Product Lead

> Independent portfolio project. Users are [hypothetical target personas](personas.md), not researched users. All figures are projections on a synthetic dataset — see [NUMBERS.md](NUMBERS.md).

---

## 1. Problem statement

A BNPL lender earns a merchant fee on every approved transaction and absorbs unrecovered principal when a customer defaults. Whether the business makes money is therefore decided almost entirely by the approval policy.

Conventional underwriting approves on credit score. On the modelled portfolio, a credit-score-≥-600 policy approves 78.28% of applications and loses **$141,629** against $468,326 of fee revenue.

Credit score is one general-purpose signal. It ignores installment count, merchant category and employment status, each of which carries independent default signal here. That omission is the **risk-adjustment gap**, and it concentrates: two of ten categories are profitable, **Travel alone is 41.5% of the $426,283 category loss**, and four categories are 90.2% of it — uniformly large-ticket, high-default, low-fee-rate business.

The people who must act on this — risk, product, finance, executive — cannot see it. The analysis lives in SQL and notebooks. There is no way to ask *what happens if we approve differently*, and no way to compare answers on consistent terms.

## 2. Business objective

Enable a lending-policy decision to be made from evidence, with the trade-off quantified and the assumptions exposed, in minutes rather than in an analyst's week.

## 3. Product goal

A decision-support platform that lets a stakeholder move from *the book is losing money* to *here is the policy I recommend and here is what it costs* in a single session, without writing a query and without taking any number on trust.

**Explicit non-goal: the platform does not make lending decisions.** It has no write path to any approval system. Every output is a projection for a human to act on or reject.

## 4. Target users

[Risk Analyst](personas.md#p1--risk-analyst--where-is-the-loss-coming-from), [Product Manager](personas.md#p2--product-manager--what-should-we-change-and-what-breaks-if-we-do), [Finance Manager](personas.md#p3--finance-manager--what-does-this-assume-and-what-if-its-wrong), [Executive](personas.md#p4--executive--whats-the-problem-what-do-you-recommend-what-does-it-cost). All hypothetical.

## 5. Success metrics

| # | Metric | Target | Actual |
|---|---|---|---|
| M1 | Time to identify the loss-driving categories | < 30s, unaided | Met — ranked on first screen |
| M2 | Strategies comparable on consistent metrics | ≥ 4 | 4 |
| M3 | Assumptions adjustable without code change | ≥ 3 | 3 (LGD, approval floor, baseline cutoff) |
| M4 | Financial logic under test | 100% of revenue/loss/profit/simulation paths | 40 tests |
| M5 | Every projection carries its caveats | 100% of API responses | Met |
| M6 | Headline figures reproducible from a clean clone | Exactly | Met |
| M7 | UAT pass rate | ≥ 90% | See [UAT](uat-plan.md) |

## 6. Scope

**In.** Portfolio profitability · merchant-category loss attribution · RFM-style segmentation · default-risk scoring with SHAP explanation · out-of-fold strategy simulation · four-strategy comparison ladder · executive decision summary · assumption sensitivity · data validation · financial-logic tests · UAT.

**Out.** Automated or real-time lending decisions · customer-facing application · real customer or transaction data · authentication and multi-tenancy · production deployment · regulatory adverse-action compliance · collections workflow · risk-based pricing engine *(the identified next lever, deliberately deferred — see [roadmap](roadmap.md))* · model retraining pipeline · A/B testing infrastructure.

---

## 7. Functional requirements

| ID | Requirement | Priority | Persona | Acceptance | Status |
|---|---|---|---|---|---|
| **FR-01** | Present the portfolio's net position — volume, fee revenue, default losses, net profit, default rate — with the loss and its top drivers legible on first view | Must | P4, P1 | Executive dashboard loads all six metrics plus ranked category contribution without interaction | ✅ |
| **FR-02** | Attribute net profit and loss to each of the ten merchant categories, showing volume, fee revenue, losses, net profit, margin and default rate | Must | P1 | Category profits sum to portfolio profit (test-asserted); table sorts on every column | ✅ |
| **FR-03** | Let the user filter and sort category and risk data, and drill from portfolio aggregate into category detail | Must | P1 | Sort on any column; filter by profitability and default rate; drill-through preserves context | ✅ |
| **FR-04** | Segment customers into business-readable cohorts with per-segment default rate and spend | Should | P1, P2 | Four RFM-style segments partition the customer base exactly (test-asserted) | ✅ |
| **FR-05** | Score default probability for a proposed transaction and return a risk tier with a recommended action | Must | P1, P2 | `POST /api/risk/score` returns probability, tier and action; invalid input rejected with 422 | ✅ |
| **FR-06** | Simulate approval strategies across a threshold grid using **out-of-fold** model scores, reporting approval rate, volume retained, approved default rate, revenue, losses and profit at each point | Must | P2 | Grid spans 0.005–0.65, finest where the profit curve turns; misaligned score vectors rejected | ✅ |
| **FR-07** | Report **four** named strategies spanning the profit/volume trade-off, recommend one by a stated objective, and label which meet the volume floor | Must | P2, P4 | Volume-matched, break-even, constrained max, unconstrained max — each with profit vs baseline and approval-rate delta | ✅ |
| **FR-08** | Let the user vary loss-given-default, the approval-volume floor and the baseline credit cutoff, recomputing every downstream figure | Must | P2, P3 | All three exposed as API parameters and UI controls; results recompute end to end | ✅ |
| **FR-09** | Compare any selected strategies side by side against **both** baselines on identical metrics | Must | P1, P2, P3 | Comparison table renders ≥ 2 strategies plus legacy and approve-all baselines | ✅ |
| **FR-10** | Produce a decision summary answering: the problem, its cause, the options, the recommendation, the projected impact, the risks, the assumptions and the next steps | Must | P4, P3 | All eight sections populated from live API data, no hardcoded values | ✅ |
| **FR-11** | Surface the standing caveats and the assumption set with every projection, and flag when a boundary optimum or an infeasible volume floor occurs | Must | P3, P4 | `caveats`, `assumptions`, `boundary_optimum`, `volume_floor_feasible` present in every optimisation response and rendered in the UI | ✅ |
| **FR-12** | Explain an individual risk score via SHAP feature contributions | Should | P1 | `GET /api/explainability/{id}` returns base value and ranked contributions | ✅ |

**Twelve requirements.** Scoped to what four personas need to reach a decision — not an exhaustive enumeration of what the system could do.

---

## 8. Non-functional requirements

| ID | Requirement | Target | Status |
|---|---|---|---|
| NFR-01 | **Reproducibility** — every published figure regenerable from a clean clone | Byte-identical dataset from seed 42; documented command sequence | ✅ |
| NFR-02 | **Correctness under test** — financial logic asserted against hand-computed values, never against program output | 40 tests; no test pins a headline figure | ✅ |
| NFR-03 | **Honest evaluation** — no model may score rows it trained on when simulating policy | 5-fold out-of-fold scoring; row alignment enforced at runtime | ✅ |
| NFR-04 | **Assumption transparency** — no profit figure may be returned without its assumptions | `assumptions` and `caveats` on every optimisation response | ✅ |
| NFR-05 | **Performance** — dashboard interaction feels immediate | Cached DataFrames and precomputed OOF scores; no per-request training | ✅ |
| NFR-06 | **Usability** — readable by a non-analyst | Explicit loading, error and empty states; retry on every failed fetch | ✅ |
| NFR-07 | **Accessibility** — meaning never carried by colour alone | Sign glyphs and labels accompany every positive/negative value | ✅ |
| NFR-08 | **Responsiveness** — usable from 400px | Layouts reflow to single column; tables scroll horizontally in isolation | ✅ |
| NFR-09 | **Failure legibility** — operational errors explain the fix | Model-version and torn-write failures return 503 with remediation steps | ✅ |
| NFR-10 | **Maintainability** — assumptions configurable, not embedded | All economic assumptions in `config.py`; none hardcoded in analytics | ✅ |

---

## 9. Assumptions

Carried from the [charter](project-charter.md#8-assumptions); restated because they bound every requirement above.

| A1 | Fee revenue is earned at transaction time and not clawed back on later default. |
|---|---|
| **A2** | **65% LGD** — an assumption, published with 45–85% sensitivity. |
| **A3** | The synthetic default process is a defensible caricature of BNPL behaviour, not a calibrated model. |
| **A4** | Strategy evaluation is a **backtest**: policy applied on out-of-fold probability, losses realised from actual outcomes. |
| **A5** | Declining forgoes the fee entirely — no substitution to another term or product. |
| **A6** | Credit score ≥ 600 is a reasonable stand-in for conventional underwriting. |

## 10. Constraints

| C1 | Three days, one contributor. |
|---|---|
| **C2** | Synthetic data only — no real BNPL data is lawfully obtainable for a portfolio project. This is the binding constraint on every claim. |
| **C3** | No access to BNPL practitioners; personas are reasoned constructs. |
| **C4** | LGD is unmeasurable here; it can only be assumed and stress-tested. |
| **C5** | Existing codebase extended, not rebuilt. |
| **C6** | Local execution only — no cloud deployment, no auth, no persistence beyond generated artefacts. |

## 11. Open questions

| Q1 | Does the risk-adjustment gap hold on real BNPL data, or is it an artefact of the generator's default process? **Unanswerable within this project.** |
|---|---|
| **Q2** | What LGD do real BNPL lenders experience? The headline figure is highly sensitive to it. |
| **Q3** | Would risk-based pricing outperform decline-only policy? The analysis suggests yes — the book cannot reach break-even above 68% approval by declining alone — but it is untested. First item on the [roadmap](roadmap.md). |
| **Q4** | What approval-rate floor would a real BNPL business actually accept? Set at 75% here by assumption; the recommendation is sensitive to it. |
