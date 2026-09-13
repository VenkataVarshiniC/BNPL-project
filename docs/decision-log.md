# Decision Log

Six decisions that changed what the product is or what it claims. Each records the options actually weighed and the trade-off accepted.

> **No stakeholder meetings took place.** This is a solo project — see the [stakeholder register](stakeholder-register.md). Every decision below was made by one person, which is precisely why they are written down: there was no second party to challenge them, so the reasoning has to be inspectable instead.

---

## DEC-01 — Replace the approve-all baseline with a credit-score policy

**Date** 12 Sep 2026 · **Status** Implemented · **Related** [R-05](risk-register.md#r-05)

**Context.** The project reported an improvement measured against "approve every application." That baseline loses $422,614. No BNPL lender approves 100% of applications, so the comparison overstated the achievement by the entire cost of a policy nobody operates.

**Options considered**

| | Option | Assessment |
|---|---|---|
| A | Keep approve-all | Largest headline number. Indefensible the moment someone asks what the baseline is. |
| B | Credit-score cutoff as baseline | Realistic, and the gap it exposes *is* the project's thesis. Cuts the headline by ~$280K. |
| C | Industry-average default rate as baseline | Most externally credible, but requires real benchmark data that doesn't exist here. |
| D | Both, clearly labelled | Keeps the reference point without letting it headline. |

**Selected: B + D.** Credit score ≥ 600 is the baseline for every improvement claim; approve-all is retained as a labelled reference for gross book economics only.

**Rationale.** The baseline *is* the argument. A credit-score cutoff ignores installment count, merchant category and employment status — and that omission is the risk-adjustment gap the whole project is about. Choosing it made the number smaller and the story sharper.

**Trade-off accepted.** The headline improvement fell from roughly $484K to $149K. A weaker number that survives the first question beats a stronger one that doesn't.

---

## DEC-02 — Score out-of-fold rather than in-sample

**Date** 12 Sep 2026 · **Status** Implemented · **Related** [R-04](risk-register.md#r-04)

**Context.** The threshold simulation scored all 42,000 transactions with a model trained on 33,600 of them. The simulated "approved" population was partly composed of rows whose outcomes the model had memorised.

**Options considered**

| | Option | Assessment |
|---|---|---|
| A | Leave as-is | Free, and nobody might notice. Inflates every projection by an unknown margin. |
| B | Simulate on the 8,400-row holdout only | Correct but noisy, and requires scaling to portfolio level — introducing its own distortion. |
| C | Five-fold out-of-fold predictions for all 42,000 rows | Every row scored by a model that never saw it. Costs five full trainings. |

**Selected: C.**

**Rationale.** The simulation asks a counterfactual — *what if we had declined these?* Answering it with predictions that have already seen the answers isn't a weaker estimate, it's a different question. Option B keeps the full-portfolio framing only by extrapolating from a fifth of the data.

**Trade-off accepted.** Training takes roughly five times longer. Mitigated by computing once at training time and persisting to `oof_scores.npy` rather than per request. The correction cost $8,631 of projected profit — the profit maximum fell from $70,006 to $61,374.

---

## DEC-03 — Report a strategy ladder instead of one optimum

**Date** 12 Sep 2026 · **Status** Implemented · **Related** [R-03](risk-register.md#r-03)

**Context.** The profit-maximising threshold approves 36.77% of the book. It is the correct answer to "maximise profit" and an unshippable answer to "what should we do."

**Options considered**

| | Option | Assessment |
|---|---|---|
| A | Report the optimum as-is | Simple, clean, and recommends declining two thirds of applications. |
| B | Add a volume constraint and report one constrained optimum | Shippable, but buries the trade-off inside an assumption the reader can't see. |
| C | Report four named strategies spanning the trade-off | Shows the decision instead of making it invisible. More to explain. |
| D | Add risk-based pricing as an alternative lever | Probably the right long-term answer. Not deliverable in the time available. |

**Selected: C**, with D recorded as the top item on the [forward backlog](product-backlog.md#forward-backlog--not-built).

**Rationale.** A product manager owns the volume-versus-margin trade-off. Collapsing it into a single number doesn't help them decide — it decides for them and hides the fact that a choice was made. Four strategies make the frontier visible: what better selection is worth at constant volume, what stopping the loss costs, and where the theoretical ceiling sits.

**Trade-off accepted.** The product no longer gives one clean answer. That is the intended outcome, and the recommendation rule is stated explicitly so it can be disagreed with.

---

## DEC-04 — Recommend by "maximum volume subject to not losing money"

**Date** 12 Sep 2026 · **Status** Implemented · **Related** [DEC-03](#dec-03)

**Context.** Having decided to report four strategies, one still has to be recommended. Which objective?

**Options considered**

| | Option | Assessment |
|---|---|---|
| A | Maximise profit | 36.77% approval. Rejected — see DEC-03. |
| B | Maximise profit subject to a volume floor | Requires a floor nobody has agreed. On this portfolio, still loses $41,115 at a 75% floor. |
| C | Maximise volume subject to non-negative profit | Stops the loss with the smallest reduction in lending. Lands at 67.53% approval, +$7,588. |
| D | Match the current approval rate exactly | Isolates selection value cleanly, but leaves the book losing $60,956. |

**Selected: C**, with B and D both reported as named strategies.

**Rationale.** The problem statement is "the book is losing money," so the objective should be *stop losing money*, and among the strategies that achieve it, prefer the one that gives up least volume. It is explainable in one sentence to someone who will never read the model.

**Trade-off accepted.** C forgoes $53,787 of achievable profit relative to the unconstrained maximum, and falls 7.5pp below the configured volume floor — so the recommendation deliberately violates a constraint the product also reports. That tension is surfaced via `volume_floor_feasible: false` rather than resolved by quietly moving the floor. The objective is a business judgement made unilaterally; a different volume appetite selects a different row.

---

## DEC-05 — Build decision support, not a decisioning system

**Date** 12 Sep 2026 · **Status** Implemented · **Related** [R-09](risk-register.md#r-09)

**Context.** The risk model could plausibly be wired to approve or decline transactions automatically. Should it be?

**Options considered**

| | Option | Assessment |
|---|---|---|
| A | Automated approve/decline endpoint | Demos well. Attracts ECOA/FCRA obligations — adverse-action codes, fairness testing, model governance — that this project satisfies none of. |
| B | Decision support only, no write path | Honest about what has actually been validated. Less impressive-sounding. |
| C | Automated with a human-review queue | Hybrid, but still a decisioning system wearing a safety belt. |

**Selected: B.**

**Rationale.** Claiming automated lending decisions from a model with AUC 0.708, trained on synthetic data, validated by nobody independent, with no adverse-action capability, would be claiming something untrue. The scope boundary is a deliberate product decision, not a shortfall — and it is stated that way in the charter, the PRD and the UI itself.

**Trade-off accepted.** "Decision-support platform" is a less exciting phrase than "AI underwriting engine." It is the accurate one. The risk endpoint returns advisory language and there is no write path to any approval system.

---

## DEC-06 — Lift economic assumptions into configuration

**Date** 12 Sep 2026 · **Status** Implemented · **Related** [R-02](risk-register.md#r-02)

**Context.** Loss-given-default appeared as a bare `* 0.65` in three places in the analytics code, undocumented and unchangeable, driving every loss figure in the product.

**Options considered**

| | Option | Assessment |
|---|---|---|
| A | Leave hardcoded, document in the README | Zero effort. The assumption stays invisible at the point it's used. |
| B | Single named constant | Better, still not variable at runtime. |
| C | Configuration + API parameter + UI control + returned with every response | The assumption travels with the number it produced. |

**Selected: C**, for LGD, the volume floor and the baseline credit cutoff.

**Rationale.** A finance stakeholder's first question is "what if 65% is wrong?" — and the only satisfying answer is one they can check themselves. Returning `assumptions` on every API response means a projection cannot be separated from its assumptions in transit, even by copy-paste. Making the recommendation itself move when LGD changes is what proves the controls are real rather than decorative.

**Trade-off accepted.** More surface area to test, and the possibility of a reader generating figures that no longer match the published number set. Mitigated by a visible "assumptions changed from the documented base case" warning in the UI.

---

## Pattern

Five of these six decisions made the project's headline number **smaller** or its claims narrower: a harder baseline, honest scoring, a constrained objective, a decision-support boundary, and assumptions a reader can move against you.

That was the point. The version of this project with the biggest number was the version that fell apart under the first question.
