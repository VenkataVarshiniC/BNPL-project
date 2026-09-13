# User Stories

15 stories across 7 epics. Points on a modified Fibonacci scale (1, 2, 3, 5, 8) sized relative to each other, not to calendar time. MoSCoW priority.

> Personas referenced are [hypothetical target users](personas.md). Acceptance criteria describe the delivered MVP.

**Totals** — 61 points · 11 Must, 3 Should, 1 Could · 15 of 15 delivered

---

## Epic 1 — Portfolio Overview

### US-01 · Understand the portfolio position at a glance
**Must** · 3 pts · P4 Executive

> As an **Executive**, I want the portfolio's net position and its largest loss drivers on the first screen, so that I can grasp the scale and shape of the problem before asking anyone a question.

**Acceptance**
- Volume, fee revenue, default losses, net profit, default rate and margin render without interaction
- Net profit is visually distinguished as a loss by more than colour alone
- The loss-driving categories are ranked and visible on the same screen
- Loading, error and empty states are explicit; a failed fetch offers retry

*FR-01, NFR-06, NFR-07* · ✅

### US-02 · Trace the headline number to its inputs
**Must** · 2 pts · P3 Finance

> As a **Finance Manager**, I want revenue and expected loss reported separately from net profit, so that I can see which side of the equation is failing rather than only that it is.

**Acceptance**
- Fee revenue, default losses and net profit are three distinct figures
- The LGD assumption behind the loss figure is displayed with it
- Margin is expressed against gross volume, and the denominator is stated

*FR-01, NFR-04* · ✅

---

## Epic 2 — Risk Analysis

### US-03 · Identify the categories driving the loss
**Must** · 5 pts · P1 Risk Analyst

> As a **Risk Analyst**, I want merchant categories ranked by net profit with default rate beside it, so that I can investigate the largest portfolio risk drivers rather than the noisiest ones.

**Acceptance**
- All 10 categories show volume, fee revenue, losses, net profit, margin and default rate
- Sorted by net profit by default, ascending from worst
- Category net profits sum to portfolio net profit — asserted in test, not asserted in prose
- Profitable and loss-making categories are visually separated

*FR-02* · ✅

### US-04 · Filter and sort to test a hypothesis
**Must** · 3 pts · P1 Risk Analyst

> As a **Risk Analyst**, I want to sort and filter the category table on any metric, so that I can check whether high default rate or high ticket size is the better explanation of the loss.

**Acceptance**
- Every numeric column sorts ascending and descending
- Filters for profitable-only, loss-making-only and default rate above a threshold
- Active filters are visible and clearable in one action
- An empty filter result states that no rows match rather than rendering blank

*FR-03* · ✅

### US-05 · Read a written explanation of what is driving the loss
**Should** · 3 pts · P1, P4

> As an **Executive**, I want a short written explanation of what is causing the loss, so that I can repeat it accurately to someone who has not seen the dashboard.

**Acceptance**
- Explanation is generated from live figures, not hardcoded
- Names the top contributing categories and their share of total loss
- States the mechanism — large ticket, elevated default rate, fee rate that does not compensate
- Updates when the LGD assumption changes

*FR-02, FR-11* · ✅

### US-06 · Understand who the risky customers are
**Should** · 3 pts · P1, P2

> As a **Risk Analyst**, I want customers grouped into readable cohorts with default rate and spend, so that I can tell whether risk is concentrated in a segment or spread across the book.

**Acceptance**
- Four RFM-style segments, business-readable names
- Customer count, average income, credit score, transaction count, spend and default rate per segment
- Segments partition the customer base exactly — test-asserted

*FR-04* · ✅

---

## Epic 3 — Merchant Analysis

### US-07 · Drill from portfolio into a single category
**Must** · 3 pts · P1

> As a **Risk Analyst**, I want to drill from the portfolio view into one category's detail, so that I can investigate a driver without rebuilding the context by hand.

**Acceptance**
- Selecting a category opens its detail with the filter context preserved
- Detail shows the category's contribution as a share of total portfolio loss
- Returning to the overview restores the prior sort and filter state

*FR-02, FR-03* · ✅

### US-08 · Score a proposed transaction
**Must** · 3 pts · P1, P2

> As a **Risk Analyst**, I want to score a hypothetical transaction, so that I can sanity-check the model against cases where I already have an intuition.

**Acceptance**
- Accepts customer, amount, installment count and merchant category
- Returns default probability, risk tier and recommended action
- Rejects invalid input — non-positive amount, unknown category, out-of-range installments — with a 422 and a usable message
- The recommended action is advisory language, never an approval instruction

*FR-05* · ✅

### US-09 · See why a score is what it is
**Could** · 3 pts · P1

> As a **Risk Analyst**, I want the feature contributions behind an individual score, so that I can judge whether the model is reasoning from sensible signals.

**Acceptance**
- Returns SHAP base value and ranked feature contributions
- Contributions are directional — which pushed risk up, which down
- Presented as model attribution, never as causal explanation

*FR-12* · ✅

---

## Epic 4 — Strategy Simulation

### US-10 · Simulate an alternative approval strategy
**Must** · 8 pts · P2 Product Manager

> As a **Product Manager**, I want to see what happens to approval rate, loss rate and profit as the approval threshold moves, so that I can find the policy change worth proposing.

**Acceptance**
- Simulates across a grid spanning 0.005–0.65, finest where the profit curve turns
- Each point reports threshold, approval rate, volume retained, approved default rate, revenue, losses and profit
- **Scores are out-of-fold** — no transaction is scored by a model that trained on it
- Misaligned score vectors are rejected at runtime rather than silently producing plausible nonsense
- A threshold that approves nothing produces no point, not a row of zeroes

*FR-06, NFR-03* · ✅

### US-11 · Change the assumptions and see the answer move
**Must** · 5 pts · P2, P3

> As a **Finance Manager**, I want to vary loss-given-default, the approval-volume floor and the baseline credit cutoff, so that I can find out whether the recommendation survives my assumptions rather than the author's.

**Acceptance**
- All three adjustable from the UI; every downstream figure recomputes
- Current assumption values displayed alongside results at all times
- The recommendation itself changes when assumptions change — it is not fixed text
- Sensitivity across the plausible LGD range is available without manual re-running

*FR-08, NFR-04, NFR-10* · ✅

### US-12 · Detect when an optimum is an artefact of the search
**Must** · 3 pts · P3, P2

> As a **Finance Manager**, I want to be told when the reported optimum sits on the edge of the search grid, so that I do not present a grid boundary as a business conclusion.

**Acceptance**
- The grid extends well below any plausible operating point
- `boundary_optimum` is returned with every simulation and surfaced in the UI
- When true, a caveat states the optimum may be a grid artefact

*FR-06, FR-11* · ✅

---

## Epic 5 — Scenario Comparison

### US-13 · Compare strategies on consistent terms
**Must** · 8 pts · P2, P3

> As a **Product Manager**, I want several named strategies compared side by side against the same baseline on the same metrics, so that I can choose between real options instead of accepting one optimiser's answer.

**Acceptance**
- Four named strategies: risk-adjusted at current volume, break-even, most profitable above the floor, maximum profit
- Both baselines shown — legacy credit-score policy and approve-all
- Each strategy reports profit against the legacy baseline and its approval-rate delta in percentage points
- Each is flagged for whether it meets the volume floor
- The recommended strategy is marked, and the objective that selected it is stated
- The maximum-profit strategy is explicitly labelled an upper bound, not a recommendation

*FR-07, FR-09* · ✅

### US-14 · Separate better selection from less lending
**Must** · 5 pts · P2

> As a **Product Manager**, I want a comparison that holds approval rate constant against the current policy, so that I can tell how much of the gain comes from scoring better rather than from lending less.

**Acceptance**
- A volume-matched strategy is computed at the legacy policy's own approval rate
- Its improvement is attributable purely to selection, with approval-rate delta near zero
- The difference between this and the profit-maximising strategy is visible and explained

*FR-07, FR-09* · ✅

---

## Epic 6 — Executive Decision Support

### US-15 · Get a recommendation with its cost stated
**Must** · 5 pts · P4 Executive

> As an **Executive**, I want one recommendation with its projected impact, its trade-off, its risks and its assumptions, so that I can approve it, reject it, or say exactly what I need in order to decide.

**Acceptance**
- Eight sections: problem, cause, options, recommendation, projected impact, risks, assumptions, next steps
- Populated entirely from live API data — no hardcoded figures anywhere
- The recommendation names the profit gained **and** the approval volume forgone
- Standing caveats are shown, not linked to
- No language implies the projection is realised, guaranteed or measured

*FR-10, FR-11* · ✅

---

## Epic 7 — Testing & Documentation

Covered by [NFR-01 to NFR-10](PRD.md#8-non-functional-requirements), the [UAT plan](uat-plan.md) and the [backlog](product-backlog.md#epic-7--testing--documentation) rather than by user stories — these are engineering and governance obligations, not user-facing capability, and writing them as "as a developer I want…" would pad the story count without adding meaning.
