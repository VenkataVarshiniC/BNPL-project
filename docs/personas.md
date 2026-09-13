# Target User Personas

> **These are hypothetical target personas.** They were constructed by reasoning about the decisions each role would face at a BNPL lender. **No user interviews, surveys or observational research were conducted** — no real BNPL practitioners were available for this project. Each persona is a design instrument for prioritisation, not a research finding. Where a persona states a need, that need is an inference, and it is labelled here so it is never mistaken for evidence.

---

## P1 · Risk Analyst — "where is the loss coming from?"

**Context.** Owns portfolio credit quality. Spends most of the week in SQL and spreadsheets reconstructing which segments are underperforming, then explaining the findings to people who will not read a query.

**Decisions they own**
- Which segments to flag for policy review
- Whether a loss pattern is signal or noise
- What to recommend to the credit committee

**Needs**
- Loss attributed by merchant category, ranked, with default rate beside net profit — the two together, because either alone misleads
- Drill-down from portfolio aggregate to category detail without re-querying
- Model score distributions and how approved-population risk shifts as the threshold moves
- Assumptions visible and changeable, so a finding can be stress-tested rather than taken on faith

**Frustrations**
- Dashboards that show default rate but not profitability, so a low-default, low-margin category looks healthier than it is
- Recommendations that cannot be traced back to the calculation that produced them
- Being asked "are you sure?" with no way to answer except re-running everything

**Success.** Can name the categories driving the loss, state how much each contributes, and defend the number when challenged.

**Serves requirements** FR-02, FR-03, FR-04, FR-09 · **Primary screens** Risk Analysis, Merchant Analysis

---

## P2 · Product Manager — "what should we change, and what breaks if we do?"

**Context.** Owns the BNPL product line. Sits between risk, finance and engineering, and is accountable for a roadmap where every credit-tightening proposal competes with a growth target.

**Decisions they own**
- Which policy changes enter the roadmap and in what order
- How much approval volume the business will trade for margin
- What to tell merchants when approval rates move

**Needs**
- Side-by-side strategy comparison on consistent metrics — not one "optimal" answer
- The volume cost of every profit gain, stated explicitly in percentage points
- A like-for-like comparison holding approval rate constant, to separate *better selection* from *less lending*
- Clear labelling of which strategies are commercially shippable and which are theoretical bounds

**Frustrations**
- Optimisers that return a single number with no trade-off attached
- Analyses that quietly improve profit by shrinking the book, presented as though selection improved
- Being unable to answer "what would this do to approval rates?" in the meeting where it is asked

**Success.** Can take a recommendation to a stakeholder meeting with the trade-off quantified and the alternatives already considered.

**Serves requirements** FR-05, FR-06, FR-07, FR-08 · **Primary screens** Strategy Simulator, Scenario Comparison

---

## P3 · Finance Manager — "what does this assume, and what if it's wrong?"

**Context.** Owns the P&L forecast. Will be asked to defend any number that reaches a board pack, and is the person who discovers six months later that an assumption was load-bearing.

**Decisions they own**
- Whether a projection is credible enough to forecast against
- Which assumptions require validation before the number is used
- How much confidence to attach to a stated improvement

**Needs**
- Every assumption stated numerically and in one place, not distributed through prose
- Sensitivity analysis on the assumptions that move the answer — above all loss-given-default
- Revenue, expected loss and net profit reported separately, never collapsed into a single figure
- Explicit distinction between a backtest and a forward forecast

**Frustrations**
- Headline improvements whose baseline is undefined or conveniently weak
- Point estimates presented without a range
- Discovering that a 65% recovery assumption was the entire result

**Success.** Can state what the projection assumes, how much the answer moves if each assumption is wrong, and whether it is safe to forecast against.

**Serves requirements** FR-08, FR-09, FR-10, FR-11 · **Primary screens** Decision Summary, Strategy Simulator (assumptions panel)

---

## P4 · Executive — "what's the problem, what do you recommend, what does it cost?"

**Context.** Has four minutes. Reads the first screen and the recommendation, and will ask exactly one sceptical question.

**Decisions they own**
- Whether to approve the policy change
- Whether the trade-off is acceptable against growth commitments
- Whether the analysis is trustworthy enough to act on

**Needs**
- The problem stated in one screen: the size of the loss and what is causing it
- One recommendation, named, with its projected impact and its cost
- The major risks and the one or two assumptions that could invalidate it
- Concrete next steps rather than "further analysis recommended"

**Frustrations**
- Dashboards that present data instead of a decision
- Recommendations without a stated downside — which read as sales, not analysis
- Precision implying confidence the analysis does not have

**Success.** Can decide, or can name exactly what they need in order to decide.

**Serves requirements** FR-01, FR-07, FR-10, FR-11 · **Primary screens** Executive Dashboard, Decision Summary

---

## Persona coverage

| Requirement theme | P1 Risk | P2 Product | P3 Finance | P4 Exec |
|---|:--:|:--:|:--:|:--:|
| Portfolio position at a glance | ○ | ○ | ○ | ● |
| Loss attribution by category | ● | ○ | ○ | ○ |
| Risk drill-down and filtering | ● | ○ | | |
| Strategy simulation | ○ | ● | ○ | |
| Scenario comparison | ○ | ● | ○ | ○ |
| Assumptions and sensitivity | ○ | ○ | ● | ○ |
| Recommendation and trade-off | ○ | ● | ○ | ● |
| Caveats and limitations | ○ | ○ | ● | ○ |

● primary · ○ secondary

**Design consequence.** No single screen serves all four. The Executive Dashboard and Decision Summary are deliberately reductive — one number, one recommendation, one trade-off. The Risk Analysis and Strategy Simulator are deliberately dense. The persona split is why the product has both rather than one compromise screen that serves neither.
