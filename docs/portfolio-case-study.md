# Case Study — LedgerGuard

## How auditing my own analysis cut its headline number by two thirds, and made it defensible

**Independent portfolio project · 3 days · Solo contributor · September 2026**

---

## 1 · The problem

A Buy Now, Pay Later lender earns a merchant fee on every approved transaction and absorbs the unrecovered principal when a customer defaults. Whether the business makes money is decided almost entirely by one thing: the approval policy.

I had built a full-stack BNPL analytics application — a gradient-boosting risk model, six FastAPI endpoints, a seven-page React dashboard — and it reported a large profitability improvement from optimising the approval threshold.

Then I audited it properly. The improvement was measured against a baseline no lender operates, calculated by a model scoring transactions it had already trained on, and recommended a policy that declines two thirds of the book.

**This case study is about what I did with that.**

---

## 2 · Discovery

Before writing a line of new code, I spent a day reading the repository and — more usefully — *running* it. I regenerated the dataset, retrained the model, and reproduced every published figure from scratch.

Three of the four defects I found came from running it, not reading it.

| Claim | Reproduced? |
|---|---|
| 42,000 transactions · 5,000 customers · 10 categories | ✅ Exact |
| ~$400K projected loss | ✅ −$422,614 |
| +$70K projected profit | ✅ +$70,006 |
| **+$470K improvement** | ❌ **Reconciled to nothing** |

That last row was the thread to pull. The $470K didn't correspond to any computation in the codebase — it was arithmetic on a *rounded* baseline ($400K + $70K), while the actual delta computed to $492,620.

A number in circulation that matched nothing in the code. That was the moment the audit stopped being a formality.

---

## 3 · Analysis — four ways the project was flattering itself

### The baseline was a straw man

The improvement was measured against **"approve every application."** No BNPL lender approves 100% of applications. It's the weakest possible comparator, and choosing it inflated the headline by the entire cost of a policy nobody operates.

I built a realistic baseline: approve at credit score ≥ 600 — ignoring installment count, merchant category and employment status. That policy approves 78.28% of applications and loses **$141,629**, not $422,614.

And that omission *is* the project's thesis. Credit score is one general-purpose signal; the three it ignores each carry independent default signal. I named it the **risk-adjustment gap**, and it became the spine of the whole product.

### The simulation was leaking

`score_dataframe(merged)` scored all 42,000 transactions using a model trained on 33,600 of them. The "approved" population in every simulation was partly composed of rows whose outcomes the model had memorised.

Nothing failed. No warning appeared. The numbers were entirely plausible. That's what makes leakage dangerous — it doesn't announce itself.

I replaced it with 5-fold out-of-fold predictions: every transaction scored by a model fold that never saw it. Cost: five full trainings, computed once and persisted rather than per request. **Correction: the profit maximum fell from $70,006 to $61,374.**

I also made misalignment impossible to ignore — a score vector whose length doesn't match the transaction frame now raises, because silently producing plausible nonsense is the worst available failure mode.

### The optimum was on the edge of the map

The threshold grid started at 0.05 in steps of 0.05. The winner was 0.05, with profit still rising as the threshold fell.

That is indistinguishable from an unsearched region. The grid never tested 0.03 or 0.01, so "optimal" might just have meant "where I started looking."

I extended the search to 0.005 at 0.0025 resolution and added a `boundary_optimum` flag returned with every simulation. The optimum turned out to be **genuinely interior** at 0.0575 — the original answer was roughly right, but the original method couldn't have known that.

### The recommendation was commercially illiterate

The profit-maximising threshold approves **36.77%** of the book.

No BNPL lender ships that. It destroys merchant relationships, gross volume and customer growth — none of which appear in the objective function. The model wasn't wrong; the objective was incomplete.

**This was the most important finding in the project**, and it was a product problem, not a modelling one.

---

## 4 · Stakeholders

Four [target personas](personas.md), reasoned from the decisions each role owns. No user research — no BNPL practitioners were available, and the documents say so.

What matters is that stakeholder analysis that changes nothing is decoration. Three concrete design decisions came directly out of it:

- **Four strategies instead of one optimum** — because a Product Manager owns the volume/margin trade-off, and a single number makes that decision invisible.
- **An approval-volume floor** — because merchant partners and customers bear the cost of a profit-maximising policy that a P&L alone would never surface.
- **Assumptions returned with every API response** — because a Finance Manager cannot forecast against a number whose assumptions can be separated from it in transit.

---

## 5 · Requirements

12 functional and 10 non-functional requirements, scoped to what four personas need to reach a decision — not an enumeration of what the system could do. 15 user stories across 7 epics, 61 points.

The non-functional requirements are where the interesting constraints sit:

> **NFR-03 — Honest evaluation.** No model may score rows it trained on when simulating policy.
> **NFR-04 — Assumption transparency.** No profit figure may be returned without its assumptions.

Both are enforced in code, not by convention. The response model won't validate without `assumptions` and `caveats`.

---

## 6 · Product strategy — the decision I'm most confident about

Having found that the profit optimum was unshippable, I had to decide what the product should actually recommend.

| Option | Assessment |
|---|---|
| Maximise profit | 36.77% approval. Rejected. |
| Maximise profit subject to a volume floor | Buries the trade-off inside an assumption the reader can't see. |
| **Report four strategies spanning the trade-off** | **Selected.** Shows the decision instead of making it invisible. |
| Add risk-based pricing as an alternative lever | Right long-term answer. Not deliverable in three days. |

The product now reports four named strategies and recommends by a **stated objective**: *maximise approved volume subject to not losing money.*

That rule is a business judgement, not a mathematical result — so it's written down as a judgement, and all four strategies are reported so a different volume appetite can select a different row.

| Strategy | Approval | Net profit | vs baseline |
|---|---:|---:|---:|
| Risk-adjusted at current volume | 78.04% | −$60,956 | +$80,673 |
| **Break-even — recommended** ⭐ | **67.53%** | **+$7,588** | **+$149,217** |
| Most profitable above 75% floor | 75.31% | −$41,115 | +$100,514 |
| Maximum profit (upper bound) | 36.77% | +$61,374 | +$203,003 |

The first row is the one I'd lead with in a stakeholder meeting: **$80,673 of improvement available with essentially no reduction in lending volume** — the portion attributable purely to better selection. Everything beyond it is bought by lending less, and that's a different conversation.

---

## 7 · Planning

Three days, one person, with an explicit P0/P1/P2 order set before any work began.

One sequencing decision mattered more than the rest: **fix the numbers before writing any document that quotes them.** The original plan wrote the charter and PRD on day one. Reversing that — locking [NUMBERS.md](NUMBERS.md) first — meant nothing had to be rewritten when the figures moved on day two. Every subsequent document cites that one file.

---

## 8 · Development

Five product features, built on the existing application rather than replacing it. The React shell, design system and loading/error states were already good; the work was in what the screens *say*.

The hardest UI problem wasn't layout — it was **presenting a recommendation that deliberately violates one of the product's own constraints.** The recommended strategy falls 7.5pp below the configured volume floor, because holding the floor means accepting a loss. Rather than quietly moving the floor, the product returns `volume_floor_feasible: false` and states the conflict.

---

## 9 · Risk management

Nine risks registered. **Four materialised** — because they weren't forecasts, they were live defects:

| Risk | Impact | Resolution |
|---|---|---|
| Commercially invalid optimisation | Would have recommended declining 63% of the book | Four-strategy ladder + volume floor |
| In-sample scoring | Profit overstated by $8,631 | 5-fold out-of-fold scoring |
| Straw-man baseline | Headline inflated by ~$280K | Legacy credit-score baseline |
| Figures drifting between surfaces | Same fact as 41.5% and 41.9% | Single number set + automated cross-surface check |

The two highest-scoring risks stay **open and accepted**: the data is synthetic, and LGD is unmeasured. Neither is solvable here, and pretending otherwise would be worse than carrying them.

---

## 10 · Testing

**40 unit tests.** Every expected value hand-computed from a six-row fixture. **No test pins a headline figure** — a test asserting "$70,006" would convert a reproducible result into a hardcoded one and quietly block the very correction this project is about.

**10 UAT cases** executed against the live API and a real Chromium browser.

**UAT-03 failed.** It asserted the lowest simulated threshold would equal the grid floor of 0.005; it came back 0.0075. Investigation found the grid was correct — threshold 0.005 approves zero transactions and is deliberately skipped, so the lowest *simulated* point is higher than the *grid* floor. **The test was wrong, not the code.** Expectation corrected, retested, passed.

I'm recording that because a UAT log with no failures is usually one where the tests were written to agree with the code.

**Reproducibility** was verified across two scikit-learn major versions. All portfolio, baseline and category figures matched exactly; one of four strategies differed by **$1.17**; the headline was identical.

---

## 11 · Results

| | Before the audit | After |
|---|---|---|
| Baseline | Approve-all, −$422,614 | Credit-score policy, −$141,629 |
| Scoring | In-sample (leaked) | 5-fold out-of-fold |
| Output | One "optimal" threshold | Four strategies + stated objective |
| Recommendation | 36.77% approval | 67.53% approval |
| **Headline** | **~$470K** | **$149,217** |
| Tests | 0 | 40 unit + 10 UAT |

**The number got two thirds smaller. That is the result.**

The version with the biggest number was the version that fell apart under the first question. What replaced it is a recommendation with its cost stated — 10.75pp of approval volume for a swing from loss to profit — and every assumption a reader can move against me.

### The finding underneath

Declining transactions **cannot** make this book profitable at an acceptable approval rate. Every profitable strategy gets there by lending less, and the 75% volume floor is infeasible — the best threshold holding it still loses $41,115.

Which points directly at the lever I couldn't test: **risk-based pricing**. It's the top item on the forward backlog because the product's own conclusion nominates it.

---

## 12 · Lessons learned

**The baseline is the argument.** More of the original improvement came from choosing a weak comparator than from anything the model did. When a result looks large, ask what it's compared against before scrutinising the method.

**Leakage doesn't announce itself.** `score_dataframe(merged)` looks innocuous. Nothing fails, the numbers are plausible. The only defence is asking at every step: *which rows has this model already seen?*

**An optimiser will happily return a business-invalid answer.** The model was right; the objective function was incomplete. Constraints are exactly where domain judgement lives.

**Make assumptions travel with the numbers they produce.** Documentation beside a number gets lost. Documentation *inside the payload* doesn't.

**A smaller, defensible number beats a larger, fragile one.** Every correction hurt the headline. All of them were right.

---

## 13 · What I'd do differently

- **Run the inherited code before reading it.** Three of four defects surfaced from running it.
- **Derive UAT expectations from the requirement, not the implementation.** UAT-03 failed because it was written while looking at `config.py` instead of FR-06.
- **Set the volume floor from the analysis, not by assumption.** 75% was chosen before I knew the book can't break even above ~68% approval.

---

## 14 · Limitations

The dataset is **synthetic** — this demonstrates a method, not a finding about BNPL lending. **LGD is assumed at 65%**, and at 45% the problem dissolves entirely. The volume floor was set unilaterally. **No independent model validation** — in regulated lending that separation is a requirement, and there isn't one here. **No real user acceptance** — UAT was executed by the person who wrote the software.

All of which is stated in the product, not just in the documentation.

---

## 15 · Artefacts

**Product** — [Executive summary](screenshots/01-executive.png) · [Risk analysis](screenshots/02-risk-analysis.png) · [Strategy simulator](screenshots/05-simulator.png) · [Scenario comparison](screenshots/06-comparison.png) · [Decision summary](screenshots/07-decision.png)

**Project** — [Charter](project-charter.md) · [PRD](PRD.md) · [Personas](personas.md) · [User stories](user-stories.md) · [Backlog](product-backlog.md) · [Roadmap](roadmap.md) · [Stakeholders](stakeholder-register.md) · [RACI](raci.md) · [Risk register](risk-register.md) · [RAID](raid-log.md) · [Decision log](decision-log.md) · [UAT](uat-plan.md) · [Retrospective](retrospective.md) · [Architecture](architecture.md) · [NUMBERS](NUMBERS.md)

**Stack** — FastAPI · scikit-learn · pandas · SHAP · pytest · React 18 · Vite · Tailwind · Recharts · Playwright
