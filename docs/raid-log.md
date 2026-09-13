# RAID Log

Risks · Assumptions · Issues · Dependencies. Lightweight companion to the [risk register](risk-register.md), which carries the full scoring and mitigation detail.

**As at** 13 September 2026 · **Only real items are listed.** Nothing here is filler.

---

## Risks

Summary only — see the [risk register](risk-register.md) for probability, impact, mitigation and contingency.

| ID | Risk | Score | Status |
|---|---|:-:|---|
| R-01 | Synthetic data cannot support real-world claims | 20 🔴 | Open — accepted |
| R-02 | LGD assumed, not measured; drives every figure | 20 🔴 | Open — mitigated |
| R-03 | Optimisation produces a commercially invalid recommendation | 20 🔴 | Materialised — closed |
| R-04 | In-sample scoring inflates projected profit | 16 🔴 | Materialised — closed |
| R-05 | Improvement measured against a straw-man baseline | 16 🔴 | Materialised — closed |
| R-07 | No independent model validation or user acceptance | 15 🔴 | Open — accepted |
| R-06 | Figures drift between product, documents and résumé | 12 🟠 | Materialised — closed |
| R-09 | Decision support mistaken for automated decisioning | 10 🟠 | Open — mitigated |
| R-08 | Scope creep against a three-day constraint | 9 🟠 | Closed |

---

## Assumptions

Every one of these is load-bearing. If an assumption is wrong, the figures that depend on it are wrong.

| ID | Assumption | Depends on it | Validated? | If wrong |
|---|---|---|---|---|
| **A-01** | **65% of principal is unrecovered on default** | Every loss and profit figure in the product | ❌ No — chosen, not measured | At 45% the book is already profitable and the problem dissolves; at 85% it needs 47% approval. Sensitivity published across 45–85%. |
| **A-02** | A credit-score-≥-600 policy is a fair stand-in for conventional underwriting | The baseline, and therefore every improvement claim | ❌ No — reasoned, not benchmarked | The improvement figure moves. Cutoff is adjustable; at 640 the baseline is already near break-even. |
| **A-03** | 75% approval is the business's volume floor | Which strategies count as shippable | ❌ No — set unilaterally | A different appetite selects a different recommended strategy. Reported as a parameter, not a truth. |
| **A-04** | Fee revenue is earned at transaction time and not clawed back on later default | All revenue figures | ⚠️ Partly — asserted in test, not validated against real BNPL contracts | Revenue overstated; every strategy's profit falls, loss-making categories worst. |
| **A-05** | Declining a transaction forgoes its fee entirely — no substitution | The cost side of every tightening strategy | ❌ No | The cost of tightening is overstated. Recommendation becomes conservative rather than wrong. |
| **A-06** | The synthetic generator's default process resembles real BNPL behaviour | Whether any finding generalises | ❌ No — and untestable here | The method still holds; the findings say nothing about real lending. This is [R-01](risk-register.md#r-01). |
| **A-07** | Out-of-fold backtest performance approximates forward performance | The credibility of every projection | ⚠️ Partly — OOF is the correct counterfactual, but a backtest is not a forecast | Live results differ. Stated as a standing caveat on every API response. |

**Four of seven are unvalidated and cannot be validated within this project.** That is the honest summary.

---

## Issues

Things that actually went wrong. All closed.

| ID | Issue | Raised | Impact | Resolution | Status |
|---|---|---|---|---|---|
| **I-01** | Threshold simulation scored rows the model trained on | Audit, Day 1 | Projected profit overstated by $8,631 | Five-fold out-of-fold scoring; row alignment enforced at runtime — [DEC-02](decision-log.md#dec-02) | ✅ Closed |
| **I-02** | Reported optimum sat on the grid boundary, undetectable | Audit, Day 1 | Could not distinguish a real optimum from an unsearched region | Grid extended to 0.005 at 0.0025 resolution; `boundary_optimum` returned. Optimum confirmed interior | ✅ Closed |
| **I-03** | Improvement quoted against approve-all | Audit, Day 1 | Headline inflated by ~$280K | Legacy credit-score baseline added — [DEC-01](decision-log.md#dec-01) | ✅ Closed |
| **I-04** | $470K figure did not reconcile to any computation | Audit, Day 1 | A number in circulation matched nothing in the code | Traced to arithmetic on a rounded baseline. [NUMBERS.md](NUMBERS.md) established as single source | ✅ Closed |
| **I-05** | LGD hardcoded in three places | Audit, Day 1 | Load-bearing assumption invisible and unchangeable | Lifted to config, exposed as parameter and control — [DEC-06](decision-log.md#dec-06) | ✅ Closed |
| **I-06** | Zero test coverage of financial logic | Audit, Day 1 | No assertion that revenue, loss or profit were computed correctly | 40 tests against hand-computed values | ✅ Closed |
| **I-07** | Comparison page labelled a loss-making strategy "best" while the recommendation star sat elsewhere | Visual review, Day 2 | Two conflicting answers to "which one?" on one screen | Highlight now follows the recommendation; the within-floor option reframed as the tension it represents | ✅ Closed |
| **I-08** | Loss-share denominator differed between dashboard (41.5%) and NUMBERS.md (41.9%) | Screenshot review, Day 2 | Same fact, two numbers | Denominator stated explicitly; both figures published — [R-06](risk-register.md#r-06) | ✅ Closed |
| **I-09** | `.env.example` shipped with `API_HOST` / `API_PORT`, which are not Settings fields | User report, Day 3 | Pydantic rejected unknown keys; app crashed at import before any handler could explain | Corrected to real fields; `extra = "ignore"` added; two regression tests | ✅ Closed |
| **I-10** | UAT-03 failed on first execution | UAT, Day 3 | Apparent grid defect | Root-caused to an incorrect test expectation conflating grid with simulated points — [DEF-01](uat-plan.md#def-01--uat-03-failed-on-first-execution) | ✅ Closed |

**Six of ten were latent defects found by audit before any new work began.** I-07 through I-10 were introduced or exposed during the three days.

---

## Dependencies

| ID | Dependency | Type | Criticality | Status | Note |
|---|---|---|---|---|---|
| **D-01** | Out-of-fold scores must exist before the simulator can run | Internal, blocking | High | ✅ Met | Five full trainings — computed once at training time and persisted, never per request. The sequencing constraint that shaped the whole build. |
| **D-02** | Trained model must exist before any strategy simulation | Internal, blocking | High | ✅ Met | Explicit failure messages distinguish a missing model, a torn write and a version mismatch |
| **D-03** | Generated dataset must exist before training | Internal, blocking | High | ✅ Met | Seeded; reproduces byte-identically across scikit-learn versions |
| **D-04** | Frontend depends on the backend running locally | Runtime | Medium | ✅ Met | Explicit error state with retry; `.env.example` documents the base URL |
| **D-05** | scikit-learn version affects model internals | External | Medium | ✅ Verified | Reproduced across 1.5.1 and 1.8.0 — one figure differed by $1.17, the headline was identical |
| **D-06** | Locked number set must exist before any document quotes a figure | Process, blocking | High | ✅ Met | [NUMBERS.md](NUMBERS.md) written before the PRD, README or case study |
| **D-07** | Real recovery data would be required to validate A-01 | External | High | ❌ **Unmet** | Unobtainable. This is why LGD sensitivity is published rather than resolved. |
| **D-08** | Independent reviewer required for genuine UAT and model validation | External | High | ❌ **Unmet** | No second person. [R-07](risk-register.md#r-07) — accepted, not solved. |

**D-07 and D-08 are unmet and unmeetable within a solo portfolio project.** They are listed because omitting them would misrepresent what was achieved.
