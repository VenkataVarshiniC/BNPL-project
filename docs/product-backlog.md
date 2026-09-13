# Product Backlog

Seven epics, 15 delivered stories (61 points), plus a prioritised forward backlog.

> **Proposed agile delivery structure.** The sprint grouping below is a *logical* decomposition showing how this work would be sequenced by a team. **It is not a historical record** — the project was built by one person over three days, not in five sprints. The actual timeline is in the [charter](project-charter.md#10-timeline).

---

## Epic summary

| Epic | Stories | Points | Priority | Depends on | Status |
|---|---:|---:|---|---|---|
| 1 — Portfolio Overview | 2 | 5 | Must | Data + analytics engine | ✅ |
| 2 — Risk Analysis | 4 | 14 | Must / Should | Epic 1 | ✅ |
| 3 — Merchant Analysis | 3 | 9 | Must / Could | Epic 2, trained model | ✅ |
| 4 — Strategy Simulation | 3 | 16 | Must | Out-of-fold scores | ✅ |
| 5 — Scenario Comparison | 2 | 13 | Must | Epic 4, policy baselines | ✅ |
| 6 — Executive Decision Support | 1 | 5 | Must | Epics 4 and 5 | ✅ |
| 7 — Testing & Documentation | — | — | Must | All | ✅ |
| | **15** | **61** | | | |

---

## Epic 1 — Portfolio Overview
*Establish the problem. Everything else is a response to this screen.*

| ID | Story | Pri | Pts | Depends on | Acceptance | Status |
|---|---|---|---:|---|---|---|
| [US-01](user-stories.md#us-01--understand-the-portfolio-position-at-a-glance) | Portfolio position at a glance | Must | 3 | Analytics engine, loader | Six metrics + ranked drivers, no interaction; loss distinguished beyond colour; explicit loading/error/empty states | ✅ |
| [US-02](user-stories.md#us-02--trace-the-headline-number-to-its-inputs) | Revenue and loss reported separately | Must | 2 | US-01 | Three distinct figures; LGD assumption displayed with the loss; margin denominator stated | ✅ |

## Epic 2 — Risk Analysis
*Move from "we are losing money" to "here is where".*

| ID | Story | Pri | Pts | Depends on | Acceptance | Status |
|---|---|---|---:|---|---|---|
| [US-03](user-stories.md#us-03--identify-the-categories-driving-the-loss) | Rank categories by net profit | Must | 5 | Epic 1 | 10 categories, 6 metrics each; sums reconcile to portfolio (test-asserted); profitable vs loss-making visually separated | ✅ |
| [US-04](user-stories.md#us-04--filter-and-sort-to-test-a-hypothesis) | Filter and sort on any metric | Must | 3 | US-03 | Every numeric column sorts both ways; profitability and default-rate filters; empty result states why | ✅ |
| [US-05](user-stories.md#us-05--read-a-written-explanation-of-what-is-driving-the-loss) | Written loss-driver explanation | Should | 3 | US-03 | Generated from live figures; names drivers and their share; states the mechanism; updates with LGD | ✅ |
| [US-06](user-stories.md#us-06--understand-who-the-risky-customers-are) | Customer segmentation | Should | 3 | Merged dataset | Four RFM-style segments, 6 metrics each, exact partition (test-asserted) | ✅ |

## Epic 3 — Merchant Analysis
*Investigate a single driver without rebuilding context.*

| ID | Story | Pri | Pts | Depends on | Acceptance | Status |
|---|---|---|---:|---|---|---|
| [US-07](user-stories.md#us-07--drill-from-portfolio-into-a-single-category) | Category drill-through | Must | 3 | US-03, US-04 | Filter context preserved in and out; detail shows share of total loss | ✅ |
| [US-08](user-stories.md#us-08--score-a-proposed-transaction) | Score a proposed transaction | Must | 3 | Trained model | Probability, tier, action; invalid input → 422; advisory language only | ✅ |
| [US-09](user-stories.md#us-09--see-why-a-score-is-what-it-is) | SHAP score explanation | Could | 3 | US-08 | Base value + ranked directional contributions; framed as attribution, not causation | ✅ |

## Epic 4 — Strategy Simulation
*The core of the product. Everything before this describes a problem; this is the first screen that proposes doing something about it.*

| ID | Story | Pri | Pts | Depends on | Acceptance | Status |
|---|---|---|---:|---|---|---|
| [US-10](user-stories.md#us-10--simulate-an-alternative-approval-strategy) | Threshold simulation on out-of-fold scores | Must | 8 | **OOF scores persisted at train time** | Grid 0.005–0.65, finest at the turn; 7 metrics per point; misaligned vectors rejected at runtime; empty thresholds skipped | ✅ |
| [US-11](user-stories.md#us-11--change-the-assumptions-and-see-the-answer-move) | Adjustable assumptions | Must | 5 | US-10, config extraction | LGD, volume floor, baseline cutoff all adjustable; recommendation itself changes; sensitivity available without manual re-runs | ✅ |
| [US-12](user-stories.md#us-12--detect-when-an-optimum-is-an-artefact-of-the-search) | Boundary-optimum detection | Must | 3 | US-10 | Grid extends below any plausible operating point; `boundary_optimum` returned and surfaced; caveat when true | ✅ |

> **Blocking dependency.** US-10 cannot start before out-of-fold scores exist. Computing them costs five full model trainings, so they are produced once by `train_model.py` and persisted — never per request. This was the sequencing constraint that shaped the whole build.

## Epic 5 — Scenario Comparison
*Replace one optimiser's answer with a set of real options.*

| ID | Story | Pri | Pts | Depends on | Acceptance | Status |
|---|---|---|---:|---|---|---|
| [US-13](user-stories.md#us-13--compare-strategies-on-consistent-terms) | Four-strategy comparison ladder | Must | 8 | US-10, policy baselines | 4 strategies + 2 baselines on identical metrics; profit vs baseline and approval delta each; volume-floor flag; recommended one marked with its objective; max-profit labelled an upper bound | ✅ |
| [US-14](user-stories.md#us-14--separate-better-selection-from-less-lending) | Volume-matched like-for-like | Must | 5 | US-13 | Computed at the legacy policy's own approval rate; approval delta ≈ 0; difference from profit-max explained | ✅ |

## Epic 6 — Executive Decision Support
*Convert analysis into a decision someone can approve or reject.*

| ID | Story | Pri | Pts | Depends on | Acceptance | Status |
|---|---|---|---:|---|---|---|
| [US-15](user-stories.md#us-15--get-a-recommendation-with-its-cost-stated) | Decision summary | Must | 5 | Epics 4 and 5 | Eight sections from live data; profit gained **and** volume forgone; caveats shown inline; no realised-result language | ✅ |

## Epic 7 — Testing & Documentation
*Not user-facing capability. Tracked as obligations rather than padded into user stories.*

| Item | Pri | Depends on | Acceptance | Status |
|---|---|---|---|---|
| Financial-logic test suite | Must | Analytics engine | 40 tests against hand-computed values; **no test pins a headline figure** | ✅ |
| Out-of-fold scoring correctness | Must | Model pipeline | Row alignment enforced at runtime; OOF AUC reported separately from holdout | ✅ |
| Locked number set | Must | All analytics | [NUMBERS.md](NUMBERS.md) is the single source; every document cites it | ✅ |
| UAT execution | Must | Full product | 10 cases executed and honestly recorded — [uat-plan.md](uat-plan.md) | ✅ |
| Architecture documentation | Should | Full product | Components, data flow, APIs, technology trade-offs | ✅ |
| README as product case study | Must | All | Problem → finding → product → process → impact → limitations | ✅ |
| Portfolio case study | Should | All | End-to-end narrative including what went wrong | ✅ |

---

## Proposed sprint decomposition

> Logical structure only. Not how this was built.

| Sprint | Goal | Stories | Deliverable | Key risk | Definition of Done |
|---|---|---|---|---|---|
| **1** | Establish the problem and the baseline | US-01, US-02 | Portfolio view; legacy vs approve-all baselines defined | Baseline chosen weakly, inflating every later claim | Both baselines computed; figures reconcile; loss visible unaided |
| **2** | Attribute the loss | US-03, US-04, US-05, US-06 | Category attribution, filtering, segmentation | Category splits fail to reconcile to the portfolio | Category profits sum to portfolio profit under test; filters and sorts pass UAT |
| **3** | Build honest simulation | US-08, US-09, US-10, US-12 | Out-of-fold scoring, threshold grid, boundary detection | **In-sample scoring inflates every projection** | OOF scores persisted; alignment enforced; grid extends past any plausible operating point |
| **4** | Turn simulation into decision support | US-07, US-11, US-13, US-14 | Adjustable assumptions, four-strategy ladder, volume-matched comparison | **A single optimum is shipped without its trade-off** | Four strategies; volume floor enforced and its feasibility reported; recommendation objective stated |
| **5** | Decision, validation, narrative | US-15 + Epic 7 | Decision summary, UAT, documentation | Figures drift between product and documents | UAT executed and recorded; every document traces to NUMBERS.md |

---

## Forward backlog — not built

Prioritised by expected value, not by effort. The first item is the one the analysis itself points to.

| Pri | Item | Rationale | Est. |
|---|---|---|---|
| **P1** | **Risk-based pricing simulation** | The central finding is that decline-only policy cannot make the book profitable above ~68% approval. Pricing is the untested lever, and it is the only one that could hold volume *and* margin. Highest-value next step by a distance. | 13 |
| P1 | Installment-term policy simulation | Installment count carries default signal; capping terms on risky segments is a lighter-touch alternative to declining. | 8 |
| P2 | Confidence intervals on projections | Every figure is currently a point estimate. Bootstrapped intervals would let Finance forecast against a range. | 8 |
| P2 | Save, name and persist custom scenarios | Comparison is currently limited to the four computed strategies. | 5 |
| P2 | Segment-level strategy simulation | A single global threshold is crude; per-category or per-segment thresholds are how this is actually done. | 13 |
| P3 | Model comparison (XGBoost, LightGBM) | AUC 0.708 is modest, but model choice is not the binding constraint — the economics are. Low expected value. | 5 |
| P3 | Adverse-action reason codes | Required for real deployment under ECOA/FCRA. Out of scope for a portfolio project but the first compliance gap. | 8 |
| P3 | Cloud deployment | Improves demo access, not the analysis. Explicitly deprioritised. | 5 |
| P4 | Authentication and multi-user views | No value until there is more than one user and real data. | 8 |

**Deliberately rejected:** real-time approval integration *(the product is decision support by design — see [DEC-03](decision-log.md))* · autonomous AI decisioning *(same)* · collections workflow *(different problem)* · deep-learning risk model *(no signal available to justify it at this data scale)*.
