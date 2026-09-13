# UAT Plan & Execution Record

**Executed** 13 September 2026 · **Result: 10 of 10 passed, after one failure and a corrected test expectation**

> ## Who executed this, and what that means
>
> **UAT was executed by the sole contributor — the same person who wrote the software.** No independent user participated. On a real project this is [the largest methodological weakness](raci.md#where-the-gaps-are-real) in the whole exercise, and it is recorded here rather than glossed over.
>
> What this exercise can catch: broken behaviour, inconsistent figures, unhandled inputs, contradictions between screens.
>
> What it **cannot** catch: *"this does not answer the question I actually have."* That is what user acceptance testing is for, and this is not that. It is systematic verification wearing UAT's clothes.
>
> Every result below is the actual output of an executable harness (`uat_run.py`), run against the live API and a real browser. Nothing is marked passed by inspection.

---

## Method

| | |
|---|---|
| Backend | uvicorn on `127.0.0.1:8000`, production build |
| Frontend | Vite preview build on `127.0.0.1:4173` |
| Browser | Chromium via Playwright, 1500×1200 |
| Data | Synthetic, seed 42 — 5,000 customers / 42,000 transactions |
| Assumptions | LGD 65%, volume floor 75%, baseline cutoff 600 |

Nine cases assert against the API directly. UAT-10 drives a real browser and compares what a reader sees on screen against what the API returned — the failure mode that matters most for a decision-support product, since a dashboard that disagrees with its own backend is worse than no dashboard.

---

## Results

| ID | Req | Scenario | Status |
|---|---|---|:--:|
| UAT-01 | FR-01 | Portfolio endpoint returns all headline metrics | ✅ |
| UAT-02 | FR-02 | Category net profits reconcile to the portfolio total | ✅ |
| UAT-03 | FR-06 | Threshold search extends past the point where approvals run out | ✅¹ |
| UAT-04 | FR-07 | Four named strategies returned, each with trade-off fields | ✅ |
| UAT-05 | FR-07/09 | Improvement measured against the legacy baseline, not approve-all | ✅ |
| UAT-06 | FR-08 | Changing LGD recomputes baselines and the recommendation | ✅ |
| UAT-07 | FR-07/11 | Volume floor enforced and infeasibility surfaced | ✅ |
| UAT-08 | FR-05/NFR-09 | Invalid inputs rejected with 422 | ✅ |
| UAT-09 | FR-11/NFR-04 | Projections never returned without caveats and assumptions | ✅ |
| UAT-10 | FR-03/10, NFR-01 | Screen figures match the API; sort and filter work | ✅ |

¹ Failed on first execution. See the defect record below.

---

## Case detail

### UAT-01 · Portfolio metrics — PASS
**Expected** HTTP 200, nine fields present, 42,000 transactions.
**Actual** HTTP 200, no fields missing, 42,000 transactions.

### UAT-02 · Reconciliation — PASS
**Expected** 10 categories summing to the portfolio net profit of −$422,613.78.
**Actual** 10 categories summing to −$422,613.78, delta $0.00.

The single most important arithmetic check in the product. A category split that does not reconcile means the loss attribution — the entire diagnosis — is wrong.

### UAT-03 · Threshold search depth — PASS (after correction)
**Expected (corrected)** Lowest simulated threshold ≤ 0.01 approving ≤ 5 transactions; ≥ 10 points below 0.05; boundary flag returned.
**Actual** Lowest simulated threshold 0.0075 approving 1 transaction; 17 points below 0.05; `boundary_optimum: false`.

### UAT-04 · Strategy ladder — PASS
**Expected** Four strategies, each carrying profit vs baseline, approval-rate delta, volume-floor flag and rationale.
**Actual** Four strategies present, all fields populated, `recommended_strategy: breakeven`.

### UAT-05 · Improvement arithmetic — PASS
**Expected** `profit_vs_legacy == net_profit − legacy_net_profit` for every strategy.
**Actual** All four consistent to within $0.02.

Guards the specific dishonesty this project exists to avoid: quoting an improvement against a straw-man baseline.

### UAT-06 · Assumption sensitivity — PASS
**Expected** Profit falls monotonically as LGD rises; the recommendation itself changes.
**Actual** Legacy baseline +$46,049 at 45% LGD > −$141,629 at 65% > −$329,308 at 85%. Recommended threshold moved 0.105 → 0.16.

Proves the assumption controls are real rather than decorative — the recommendation moves, not just the numbers.

### UAT-07 · Volume floor — PASS
**Expected** A 95% floor is respected by `constrained_max`; feasibility flag and caveat present.
**Actual** `constrained_max` approval 95.16%, `volume_floor_feasible: false`, floor caveat present.

### UAT-08 · Invalid input — PASS
**Expected** Negative amount, out-of-range installments, missing category and LGD = 5.0 all rejected with 422.
**Actual** All four rejected with 422.

### UAT-09 · Caveats and assumptions — PASS
**Expected** Caveats present including "synthetic" and "backtest"; complete assumption set returned.
**Actual** 4 caveats, both terms present, all five assumption keys returned.

The product must be structurally incapable of returning a profit figure stripped of its qualifications.

### UAT-10 · Cross-surface consistency — PASS
**Expected** The recommended improvement ($149,217) and the legacy baseline ($141,629) appear consistently on the executive, decision and comparison screens; sorting reorders the table; filtering returns rows.
**Actual** Both figures found on all three screens. Sorting by Default rate reordered the first row. Profitable-only filter returned 2 rows.

---

## Defect record

### DEF-01 — UAT-03 failed on first execution

| | |
|---|---|
| **Raised** | 13 Sep 2026, first UAT run |
| **Severity** | Low — test defect, no product impact |
| **Status** | Closed |

**Symptom.** UAT-03 asserted that the lowest simulated threshold would be ≤ 0.005, matching `settings.threshold_grid_min`. It came back as 0.0075.

**Investigation.** The grid is built correctly: 80 points spanning 0.005 to 0.6. Threshold 0.005 approves **zero** transactions, and `simulate_thresholds` deliberately skips thresholds with an empty approved set rather than emitting a row of zeroes that would distort the chart and divide by zero. One threshold was dropped, leaving 79 simulated points with a minimum of 0.0075.

**Root cause.** The test expectation, not the product. It conflated *the grid searched* with *the points returned*. The skip behaviour is intentional and already covered by `test_empty_threshold_points_are_skipped` in the unit suite.

**Resolution.** Expectation corrected to assert the property that actually matters — that the search continued past the point where approvals run out, evidenced by the lowest simulated point approving just 1 transaction. Retested: PASS.

**Note.** This is recorded because a UAT log with no failures is usually a log where the tests were written to agree with the code. The failure was real, the investigation was real, and the outcome was that the test was wrong.

---

## Not covered

Stated so the pass rate is not read as broader assurance than it is.

- **Real user acceptance.** No independent user. Whether these screens answer a risk analyst's actual questions is untested.
- **Accessibility.** No screen-reader or keyboard-only pass. NFR-07 is asserted by construction, not verified.
- **Responsive layout.** Tested at 1500px only. NFR-08 is unverified below that.
- **Performance under load.** Single-user local only. No concurrency testing.
- **Cross-browser.** Chromium only.
- **The SHAP explainability path.** Covered by the unit suite but not exercised end to end here.
- **Model validity.** UAT confirms the numbers are computed and displayed consistently. It says nothing about whether the model is *right* — that would require real data and an independent validation function, neither of which exists here.

---

## Reproduce

With both servers running:

```bash
python uat_run.py        # exits non-zero if any case fails
```

Results are written to `uat_results.json`.
