# Product Roadmap

> ## Read this first
>
> This document contains **two different things**, and conflating them would misrepresent the project.
>
> **Actual development timeline: three days**, 10–12 September 2026, one contributor. That is the whole of it.
>
> **The eight-week roadmap below is a proposed product delivery structure** — how this product would be sequenced by a team building it properly, with discovery, validation and a real UAT cycle. **No part of it describes work that was performed over eight weeks.** It is included because sequencing a product is a project-management competency worth demonstrating, and it is labelled so it cannot be mistaken for history.

---

## Actual timeline

| Day | Date | Work | Outcome |
|---|---|---|---|
| 1 | 10 Sep 2026 | Repository audit · analytical correction · PM foundation | Three analytical defects identified and fixed; numbers locked; charter, PRD, personas, stories, backlog, roadmap, stakeholder register, RACI |
| 2 | 11 Sep 2026 | Product build | Executive dashboard, risk analysis, strategy simulator, scenario comparison, decision summary |
| 3 | 12 Sep 2026 | Governance · validation · narrative | Risk register, RAID, decision log, UAT execution, retrospective, architecture, README, case study |

**Prior to this:** an initial version of the backend, model and dashboard existed (2 commits). The three days transformed it from an analysis with a UI into a decision-support product with a defensible recommendation. What changed and why is in the [decision log](decision-log.md) and [retrospective](retrospective.md).

---

## Proposed product roadmap — 8 weeks

*Hypothetical. Not performed.*

| Wk | Phase | Objective | Key activities | Exit criteria |
|---|---|---|---|---|
| **1** | **Discovery** | Establish that the problem is real and worth solving | Interview risk, product and finance stakeholders · review current underwriting policy · quantify the loss from production data · confirm who owns the approval decision | Problem statement validated by the people who own the P&L; baseline policy documented as it actually operates |
| **2** | **Requirements** | Define what would change a decision | Persona validation against real practitioners · requirement elicitation · success metrics agreed with Finance · scope boundary agreed — **decision support, not decisioning** | PRD signed off; success metrics have owners; out-of-scope list accepted by all parties |
| **3** | **Data & Analysis** | Understand the loss before modelling it | Data quality assessment · category-level loss attribution · **LGD measured from actual recovery data rather than assumed** · driver analysis | Loss attributed and reconciled; LGD estimated with an interval; drivers identified |
| **4–5** | **Strategy Modelling** | Build a model that can be trusted to simulate policy | Feature engineering · model selection · **out-of-fold evaluation designed in from the start** · strategy objective agreed with Product and Finance · volume floor negotiated, not assumed | Model validated out-of-fold; objective function agreed in writing; boundary and feasibility checks built in |
| **6** | **MVP Development** | Make the analysis usable by non-analysts | Dashboard, risk analysis, simulator, comparison, decision summary · assumptions exposed as controls | All Must-have requirements delivered; every projection carries its assumptions |
| **7** | **Integration & Hardening** | Make the numbers defensible | Financial-logic test suite · reconciliation across every surface · sensitivity analysis · error and failure states | Tests green; figures identical across product and documents; failure modes explain their remedy |
| **8** | **UAT & Launch** | Confirm it supports a real decision | UAT with each persona · defect triage · decision review with stakeholders · handover | UAT passed; recommendation reviewed by decision owners; limitations formally accepted |

### Where the three days map onto this

Days 1–3 compressed weeks 3 through 8, minus everything requiring access to real people or real data. Weeks 1–2 (discovery, stakeholder validation) and the real-data portions of week 3 (measured LGD) **could not be performed at all** — that is constraint [C2/C3](PRD.md#10-constraints), and it is the honest boundary of what this project demonstrates.

---

## Future roadmap — post-MVP

Sequenced by what the analysis itself says matters, not by effort. Full backlog with estimates: [product-backlog.md](product-backlog.md#forward-backlog--not-built).

### Next — the lever the analysis points to

**Risk-based pricing simulation.** The central finding is that declining transactions cannot make this book profitable above roughly a 68% approval rate. Every strategy that reaches profitability does so by lending less. Pricing is the untested alternative — charging a fee rate that compensates for segment risk rather than refusing the segment — and it is the only lever that could plausibly hold both volume and margin. It is first because the product's own conclusion nominates it.

**Installment-term policy.** Installment count carries independent default signal. Capping terms on risky segments is a lighter-touch intervention than declining, and it preserves the merchant relationship.

### Then — making the numbers safer to rely on

**Confidence intervals.** Every figure is a point estimate. Finance cannot responsibly forecast against a number with no range.

**Segment-level thresholds.** A single global cutoff is crude. Real underwriting varies policy by segment, and the category-level loss concentration in this portfolio suggests it would help materially.

**Measured LGD.** The single largest source of uncertainty. At 45% the problem dissolves; at 85% the book needs a 47% approval rate. Everything downstream is conditional on a number that was assumed.

### Later — production concerns

Adverse-action reason codes (ECOA/FCRA) · model monitoring and drift detection · authentication and multi-user views · cloud deployment.

### Explicitly not planned

Real-time approval integration and autonomous decisioning. The product is decision support **by design**, not by limitation — see [DEC-03](decision-log.md). Building toward automated lending would require model governance, fairness testing, adverse-action infrastructure and regulatory review that no portfolio project can honestly claim.
