# Risk Register

**Scored** Probability × Impact, each 1–5. Score ≥ 15 red, 8–14 amber, ≤ 7 green.
**Owner** roles, not people — see [RACI](raci.md). One contributor held every role.

> Four of these nine risks **materialised** during the project. Those are marked and cross-referenced to what was actually done about them. A register of hypothetical risks that never happened is a planning artefact; this one is partly an incident log.

---

## Summary

| ID | Risk | P | I | Score | Status |
|---|---|:-:|:-:|:-:|---|
| [R-01](#r-01) | Synthetic data cannot support real-world claims | 5 | 4 | **20** 🔴 | Open — accepted |
| [R-02](#r-02) | LGD is assumed, not measured, and drives every figure | 5 | 4 | **20** 🔴 | Open — mitigated |
| [R-03](#r-03) | Optimisation produces a commercially invalid recommendation | 4 | 5 | **20** 🔴 | **Materialised** — closed |
| [R-04](#r-04) | In-sample scoring inflates projected profit | 4 | 4 | **16** 🔴 | **Materialised** — closed |
| [R-05](#r-05) | Improvement measured against a straw-man baseline | 4 | 4 | **16** 🔴 | **Materialised** — closed |
| [R-06](#r-06) | Figures drift between product, documents and résumé | 4 | 3 | **12** 🟠 | **Materialised** — closed |
| [R-07](#r-07) | No independent model validation or user acceptance | 5 | 3 | **15** 🔴 | Open — accepted |
| [R-08](#r-08) | Scope creep against a three-day constraint | 3 | 3 | **9** 🟠 | Closed |
| [R-09](#r-09) | Decision support mistaken for automated decisioning | 2 | 5 | **10** 🟠 | Open — mitigated |

---

### R-01
**Synthetic data cannot support real-world claims** · P5 × I4 = **20** · Owner: Project/Product Lead · *Open — accepted*

No real BNPL transaction data is lawfully obtainable for a portfolio project, so every figure describes a generated portfolio. The risk is that a reader — or the author — quietly starts treating the findings as evidence about real BNPL lending.

**Mitigation.** The word "synthetic" is embedded in the API response itself: `assumptions.dataset` and a standing caveat are returned with every projection, so a figure cannot be quoted without it. The generator is committed and seeded, so anyone can inspect exactly how the data was constructed. Every document states it.

**Contingency.** None available. This is a hard constraint, not a problem to be solved.

**Residual.** High and permanent. The honest position is that this project demonstrates *method*, not *findings about BNPL*.

---

### R-02
**LGD is assumed, not measured, and drives every figure** · P5 × I4 = **20** · Owner: Risk & Finance *(vacant)* · *Open — mitigated*

Every loss figure is `defaulted principal × 0.65`. That 0.65 was chosen, not measured, by the same person who then used it — the RACI gap is real. At 45% the portfolio is already profitable and the entire problem dissolves; at 85% it needs a 47% approval rate to survive.

**Mitigation.** Lifted from three hardcoded call sites into configuration, exposed as an API parameter and a UI control, returned with every response, and published as a sensitivity table across 45–85% in [NUMBERS.md](NUMBERS.md). A reader can substitute their own assumption and watch the recommendation move.

**Contingency.** If real recovery data became available, re-run and republish. Nothing else in the pipeline changes.

**Residual.** High. Mitigation makes the dependency *visible*; it does not remove it.

---

### R-03
**Optimisation produces a commercially invalid recommendation** · P4 × I5 = **20** · Owner: Product Lead · *Materialised — closed*

> **This happened.** The unconstrained profit optimiser recommended a threshold that approves **36.77%** of the book — declining nearly two thirds of applications. It maximises modelled profit and would destroy the merchant relationships and growth the business runs on. Shipped as-is, it would have been the single most damaging thing in the project: a recommendation that is arithmetically correct and commercially illiterate.

**Resolution.** Single-optimum reporting replaced with a four-strategy ladder and a stated objective — *maximise approved volume subject to not losing money*. A configurable volume floor was added, the profit maximum is labelled an upper bound rather than a recommendation, and `volume_floor_feasible` reports when the floor and profitability are incompatible. See [DEC-03](decision-log.md#dec-03) and [DEC-04](decision-log.md#dec-04).

**Residual.** Low. The objective function is still a unilateral judgement (see [RACI](raci.md#where-the-gaps-are-real)), which is why all four strategies are reported rather than one.

---

### R-04
**In-sample scoring inflates projected profit** · P4 × I4 = **16** · Owner: Data & Analytics · *Materialised — closed*

> **This happened.** `simulate_thresholds` scored all 42,000 transactions with a model trained on 33,600 of them. The approved subset was flattered by outcomes the model had already seen, so projected profit was optimistic by an unmeasured margin.

**Resolution.** Five-fold out-of-fold predictions computed once at training time and persisted; the simulator uses only those. Row alignment is enforced at runtime — a misaligned score vector raises rather than silently producing plausible nonsense. Corrected the profit maximum from **$70,006 to $61,374**, a 12.3% overstatement of the corrected figure.

**Residual.** Low. Out-of-fold scoring is the correct counterfactual for a backtest. The remaining limitation — that this is a backtest and not a forward forecast — is a standing caveat.

---

### R-05
**Improvement measured against a straw-man baseline** · P4 × I4 = **16** · Owner: Product Lead · *Materialised — closed*

> **This happened.** The improvement was quoted against "approve every application" — a policy no lender operates. That inflated the headline by the entire cost of the straw man: the real current-state policy loses **$141,629**, not $422,614.

**Resolution.** Added `legacy_policy_baseline` (credit score ≥ 600, ignoring installment count, category and employment) as the comparator. Approve-all retained but explicitly labelled reference-only, with a code comment stating it must never headline an improvement claim. A "risk-adjusted at current volume" strategy was added so the portion attributable to *better selection* can be separated from the portion bought by *lending less*. Asserted in [UAT-05](uat-plan.md#uat-05--improvement-arithmetic--pass).

**Residual.** Low. The credit-score-600 baseline is itself an assumption, and it is adjustable.

---

### R-06
**Figures drift between product, documents and résumé** · P4 × I3 = **12** · Owner: Project Lead · *Materialised — closed*

> **This happened twice.** The dashboard computed Travel's share of loss against the sum of loss-making categories (41.5%) while NUMBERS.md used the portfolio net figure (41.9%) — both defensible, but inconsistent. Separately, an early UAT case quoted a 95.7% approval rate that was actually 95.16%.

**Resolution.** [NUMBERS.md](NUMBERS.md) established as the single source every document cites, with denominators stated explicitly. [UAT-10](uat-plan.md#uat-10--cross-surface-consistency--pass) drives a real browser and asserts that headline figures appearing on screen match the API response.

**Residual.** Medium. Automated checking covers the two headline figures across three screens; the rest depends on discipline.

---

### R-07
**No independent model validation or user acceptance** · P5 × I3 = **15** · Owner: Risk & Finance / End User *(both vacant)* · *Open — accepted*

The model was built and validated by the same person. UAT was executed by the person who wrote the software. In regulated lending, separating model development from model validation is a **requirement**, precisely because a developer validating their own work is not a control.

**Mitigation.** Stated plainly in the [RACI](raci.md#where-the-gaps-are-real) and at the top of the [UAT record](uat-plan.md). Out-of-fold evaluation and the test suite reduce — but cannot replace — independent review.

**Contingency.** None available in a solo project.

**Residual.** High and structural. This is a limitation of the exercise, not an oversight in it.

---

### R-08
**Scope creep against a three-day constraint** · P3 × I3 = **9** · Owner: Project Lead · *Closed*

With five product features and thirteen artefacts to deliver, the temptation was to add authentication, deployment, model comparison and further visualisations.

**Mitigation.** Explicit P0/P1/P2 prioritisation set before work began, with P2 items deferred by rule rather than by judgement in the moment. Deferred work is recorded in the [forward backlog](product-backlog.md#forward-backlog--not-built) with reasons, not silently dropped.

**Residual.** Low. All P0 items delivered; no P2 item was started.

---

### R-09
**Decision support mistaken for automated decisioning** · P2 × I5 = **10** · Owner: Product Lead · *Open — mitigated*

If the platform were read as making lending decisions, it would attract ECOA/FCRA obligations it does not satisfy — adverse-action reason codes, fairness testing, model governance — and a reader could reasonably conclude the project claims more than it does.

**Mitigation.** Boundary stated in the [charter](project-charter.md), [PRD](PRD.md) and on the decision summary itself. The risk endpoint returns advisory language, never approve/decline instructions. There is no write path to any approval system. The sidebar carries a permanent "decision support only" note. Adverse-action reason codes are named as the first compliance gap in the [roadmap](roadmap.md) rather than quietly omitted.

**Residual.** Low, but permanent — the framing has to be maintained in how the project is described, not just how it is built.

---

## What the register is for

Four of these nine were not forecasts. R-03, R-04, R-05 and R-06 were live defects in the project as it stood at the start of the three days — each one found by audit, each one changing the headline figure, and together they moved the claimed improvement from an indefensible ~$470K to a defensible **$149,217**.

A register that only lists what might go wrong is easy to write. The useful part is the record of what did.
