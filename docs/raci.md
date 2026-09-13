# RACI Matrix

> ## Authenticity notice
>
> **This project had one contributor.** There was no team, and no person other than the contributor performed, reviewed or approved any part of it.
>
> The matrix below maps **roles, not people**. A single individual held every role simultaneously. It is included to show which distinct responsibilities exist in delivering this kind of product, and where they would separate on a real team — not to imply that separate people held them.
>
> Where a role would normally be held by someone else, that is stated. Those gaps are real limitations of the project, and several are carried into the [risk register](risk-register.md).

**R** Responsible · **A** Accountable · **C** Consulted · **I** Informed

---

## Roles

| Role | Definition | Held by |
|---|---|---|
| **PPL** — Project/Product Lead | Scope, prioritisation, requirements, final decisions | Contributor |
| **D/A** — Data & Analytics | Data generation, modelling, financial logic, validation | Contributor |
| **ENG** — Engineering | Backend, frontend, testing, architecture | Contributor |
| **R/F** — Risk & Finance | Assumption review, objective definition, number challenge | **Vacant** — see below |
| **EU** — End User | Acceptance testing, usability feedback | **Vacant** — see below |

---

## Matrix

| Activity | PPL | D/A | ENG | R/F | EU |
|---|:--:|:--:|:--:|:--:|:--:|
| **Requirements** | | | | | |
| Problem definition | **A/R** | C | I | *C* | *C* |
| Persona definition | **A/R** | I | I | *C* | *C* |
| Requirements elicitation | **A/R** | C | C | *C* | *C* |
| Scope boundary (support vs decisioning) | **A/R** | C | C | *C* | I |
| Success metric definition | **A/R** | C | I | *A* | *C* |
| **Data & analysis** | | | | | |
| Synthetic data design | C | **A/R** | I | *C* | — |
| Loss attribution | I | **A/R** | I | *C* | I |
| Economic assumptions (LGD) | C | **R** | I | ***A*** | — |
| Assumption sensitivity | C | **A/R** | I | *C* | I |
| **Risk model** | | | | | |
| Feature selection | I | **A/R** | I | *C* | — |
| Model training | — | **A/R** | C | I | — |
| Out-of-fold evaluation design | C | **A/R** | C | *C* | — |
| Strategy objective function | **A** | **R** | I | ***C*** | *C* |
| Approval-volume floor | **A/R** | C | I | *C* | *C* |
| **Product development** | | | | | |
| API design | C | C | **A/R** | I | I |
| Frontend implementation | C | I | **A/R** | — | *C* |
| Assumption controls | **A** | C | **R** | *C* | *C* |
| Decision summary content | **A/R** | C | **R** | *C* | *C* |
| **Testing** | | | | | |
| Financial-logic tests | C | **A/R** | **R** | *C* | — |
| Reconciliation checks | I | **A/R** | C | *C* | — |
| Regression on defect fixes | I | **R** | **A/R** | I | — |
| **UAT** | | | | | |
| UAT plan authoring | **A/R** | C | C | *C* | *C* |
| **UAT execution** | **R** | I | I | I | ***A/R*** |
| Defect triage | **A/R** | C | **R** | I | *C* |
| Acceptance sign-off | **A/R** | I | I | *C* | ***A*** |
| **Launch** | | | | | |
| Documentation | **A/R** | C | C | I | I |
| Decision review | **A/R** | C | I | ***C*** | *C* |
| Limitations disclosure | **A/R** | C | I | *C* | I |
| Deployment | — | — | — | — | — |

*Italics* mark responsibilities that a real project would assign elsewhere but which were unfilled or self-assigned here.

---

## Where the gaps are real

Three rows above are not merely self-assigned — they are **structurally compromised**, and pretending otherwise would be the dishonest part of a RACI for a solo project.

**Economic assumptions — R/F should be Accountable, was vacant.**
The 65% LGD assumption drives every loss figure in the product. On a real project a Finance or Risk owner would set and defend it. Here it was chosen by the person who then used it. Mitigation: published sensitivity across 45–85% so a reader can substitute their own, and flagged as [RISK-02](risk-register.md). The mitigation does not remove the gap; it makes it visible.

**Strategy objective function — R/F should be Consulted, was vacant.**
"Maximise approved volume subject to not losing money" is a business judgement, not a technical one. It was set unilaterally. A real Product/Finance negotiation would likely land somewhere else, and the recommendation would move with it. This is why the product reports four strategies rather than embedding one objective as truth.

**UAT execution — EU should be Accountable and Responsible, was vacant.**
UAT was executed by the person who wrote the software against test cases the same person wrote. That is verification, not user acceptance. It catches defects; it cannot catch *"this does not answer the question I actually have."* The [UAT plan](uat-plan.md) records results honestly and labels them as self-executed, and the [retrospective](retrospective.md) names this as the project's largest methodological weakness.

---

## Where roles would separate on a real team

| Activity | Would move to |
|---|---|
| Economic assumptions | Finance — owns the P&L the numbers feed |
| Strategy objective | Product + Finance jointly — a commercial negotiation, not an analytical output |
| Volume floor | Product + Merchant/Commercial — the people who carry the cost of declining |
| UAT execution | Each persona independently — a user who did not build it |
| Limitations disclosure | Compliance review before any external use |
| Model validation | Independent model risk function — the standard separation in regulated lending |

The last row is the sharpest illustration. In regulated lending, model development and model validation are **required** to be separate functions precisely because a developer validating their own model is not a control. This project has no such separation and does not claim one.
