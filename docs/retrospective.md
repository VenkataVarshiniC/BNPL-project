# Project Retrospective

**13 September 2026** · Three days, one contributor

> Written to be useful rather than flattering. The most interesting thing about this project is that it started with a bigger number than it finished with.

---

## What the three days actually did

The project began as a working full-stack BNPL analytics application with a trained model, six endpoints and a seven-page React dashboard. That was already real work.

What it lacked was a defensible claim. It reported a ~$470K improvement measured against a baseline no lender operates, calculated with a model scoring transactions it had trained on, recommending a policy that declines two thirds of the book. Each of those alone would have been survivable. Together they meant the headline number could not withstand its first serious question.

Three days turned an analysis with a dashboard into a decision-support product with a recommendation that holds up. The headline fell from ~$470K to **$149,217**. That is the outcome, and it is the right direction.

---

## What went well

**The audit came first, and it earned its place.** A full day before writing any new code, spent reading the repository and *running* it — regenerating the data, retraining the model, reproducing every figure. Four material defects surfaced that way, all of which changed the headline number. Had the build started on day one, all four would have been baked into a prettier dashboard.

**Fixing the numbers before writing the documents.** The original plan wrote the PRD and charter on Day 1 and built on Day 2. Reversing that — locking the number set first — meant no document was written against figures that later moved. [NUMBERS.md](NUMBERS.md) was created before anything quoted a figure, and became the single source every other artefact cites.

**Tests written against hand-computed values.** Every expected number in the suite was calculated by hand from a six-row fixture, never copied from program output. No test pins a headline figure, so the tests can't drift into merely confirming whatever the code currently does. The one that matters most — category profits summing to the portfolio total — would have caught the entire loss attribution being wrong.

**Assumptions made movable.** Lifting LGD, the volume floor and the baseline cutoff into configuration and exposing them as controls did more for the project's credibility than any feature. A reader can set LGD to 45%, watch the problem disappear, and understand exactly how conditional the conclusion is. That is a stronger position than asserting the assumption is right.

**Cross-version reproducibility, verified by accident.** Running the pipeline on scikit-learn 1.8.0 while the project pins 1.5.1 produced identical figures except one strategy differing by $1.17. That wasn't planned, but it's a much stronger reproducibility claim than a single-environment run.

---

## What did not go well

**A config file was shipped without being run.** `.env.example` was written with `API_HOST` and `API_PORT` — plausible-sounding variables that don't exist on the Settings class. Pydantic rejected them and the app crashed at import, before any error handler existed to explain why. It cost real debugging time, and it was entirely avoidable: the file was authored from what seemed reasonable rather than from what the code actually reads.

**Two numbers described the same fact.** The dashboard computed Travel's share of loss against the sum of loss-making categories (41.5%); NUMBERS.md used the portfolio net figure (41.9%). Both are defensible; publishing both without stating the denominator is not. Caught by reading a screenshot against a document — the kind of check that only happens if someone deliberately does it.

**The comparison page contradicted itself.** It highlighted "best shippable option" on a strategy losing $41,115 while the recommendation star sat on a profitable column. Two answers to "which one?" on the same screen, produced by two pieces of logic written twenty minutes apart without either checking the other.

**A UAT case was wrong before the product was.** UAT-03 asserted the lowest *simulated* threshold would equal the *grid* floor, conflating two different things. It failed, and the investigation found the test was wrong rather than the code. A small thing, but a reminder that a test written by the author of the code inherits the author's assumptions.

**Delivery friction ate real time.** Partial zips, folder-merge uncertainty and Windows shell quoting consumed more of the three days than any analytical problem. Not intellectually interesting, but genuinely costly.

---

## Challenges

**Knowing when a smaller number is the right answer.** Every correction made the headline worse. There is a real pull toward leaving a defensible-looking figure alone, especially one already in circulation. The resolution was to keep all four framings visible with their defensibility stated, so nothing was hidden — but the temptation was real and worth naming.

**Choosing an objective function is a business judgement disguised as maths.** "Maximise volume subject to not losing money" looks like an analytical result. It isn't. It encodes a specific appetite for risk and growth that, on a real project, Product and Finance would negotiate. Making that choice alone, then documenting it as a choice rather than a finding, was the most uncomfortable decision in the project.

**Working without anyone to disagree.** No stakeholder pushed back on the volume floor. No reviewer questioned the LGD assumption. No user said the decision summary answered the wrong question. The [decision log](decision-log.md) exists to partly compensate — if nobody can challenge the reasoning in the moment, it should at least be inspectable afterwards.

---

## Lessons learned

**The baseline is the argument.** More of the original improvement figure came from choosing a weak comparator than from anything the model did. Whenever a result looks large, the first question is what it is being compared against — and that question is usually more productive than scrutinising the method.

**Leakage doesn't announce itself.** `score_dataframe(merged)` looks completely innocuous. Nothing fails, no warning appears, the numbers are plausible. The only defence is asking, at each step, *which rows has this model already seen?* — and encoding the answer as a runtime assertion.

**An optimiser will happily return a business-invalid answer.** Threshold 0.0575 maximises profit and is commercially illiterate. The model isn't wrong; the objective function was incomplete. Any optimisation over a business metric needs its constraints stated, and the constraints are exactly where domain judgement lives.

**Make assumptions travel with the numbers they produce.** Returning `assumptions` and `caveats` on every API response means a figure cannot be separated from its qualifications, even by copy-paste. Documentation that lives beside a number gets lost; documentation inside the payload doesn't.

**Config files are code.** An untested `.env.example` broke the application for a user. Anything that can crash the app at import deserves a test.

---

## What I would do differently

**Run the existing code before reading it.** The audit was thorough, but regenerating the data and reproducing the figures is what actually found three of the four defects. That should have been step one, not step four.

**Write the UAT expectations from the requirement, not from the implementation.** UAT-03 failed because it was written while looking at `config.py` rather than at FR-06. Deriving the expectation from the requirement would have produced the correct assertion first time.

**Decide the delivery mechanism before producing anything.** Partial zips created real uncertainty about whether files had been merged or replaced. A consolidated snapshot from the start — or working directly in the repository — would have removed a whole class of problem.

**Set the volume floor from the analysis rather than by assumption.** 75% was chosen before knowing that the book cannot break even above ~68% approval. A floor that turns out to be infeasible is useful information, but it would have been better as a finding than as a default the product then has to argue with.

---

## Future improvements

In priority order, with the reasoning in the [backlog](product-backlog.md#forward-backlog--not-built).

**Risk-based pricing simulation.** The central finding is that declining alone cannot make this book profitable above roughly 68% approval. Every profitable strategy gets there by lending less. Pricing — charging a fee rate that compensates for segment risk — is the only untested lever that could hold both volume and margin. The product's own conclusion nominates it.

**Measure LGD.** The single largest source of uncertainty. At 45% the problem dissolves entirely; at 85% it needs a 47% approval rate. Everything downstream is conditional on a number that was assumed.

**Confidence intervals.** Every figure is a point estimate. Finance cannot responsibly forecast against a number with no range.

**Segment-level thresholds.** A single global cutoff is crude, and the loss concentration by category suggests per-segment policy would help materially.

**Independent review.** The structural gap. Not a feature, but the thing that would most change what this project is allowed to claim.

---

## Honest summary

This project demonstrates a method, not a finding about BNPL lending. The data is synthetic, the central assumption is unmeasured, and nothing was validated by anyone other than its author.

What it does show is a specific discipline: auditing an inherited analysis, finding the ways it flattered itself, correcting them at the cost of the headline figure, and reporting the trade-off rather than the optimum. The most defensible thing in it is that the number got smaller.
