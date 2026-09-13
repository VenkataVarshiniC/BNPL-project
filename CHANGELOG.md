# Changelog

## Unreleased — 3-day transformation, complete

Turning the project from an analysis with a dashboard into a decision-support product with a defensible recommendation.

---

### The headline changed

| | Before | After |
|---|---|---|
| Baseline | Approve all — −$422,614 | Legacy credit-score policy — **−$141,629** |
| Scoring | In-sample (leaked) | **Out-of-fold, 5-fold** |
| Output | One "optimal" threshold | **Four named strategies + a stated objective** |
| Recommendation | 0.05 — declines 63% of the book | **0.105 — 67.53% approval, +$7,588** |
| Improvement claim | ~$470K (vs approve-all) | **+$149,217 (vs the real baseline)** |
| Tests | None | **40 unit + 10 UAT** |
| PM artefacts | None | **16 documents** |

The improvement figure fell because the old one was measured against a straw man and achieved by shrinking the book. The new one is smaller and survives scrutiny. See [`docs/NUMBERS.md`](docs/NUMBERS.md).

---

### Fixed — analytical defects

**Leakage in the strategy simulation.** `simulate_thresholds` scored all 42,000 transactions with a model trained on 33,600 of them, so the approved subset was flattered by outcomes the model had already seen. Now `train_model.py` computes 5-fold out-of-fold predictions once and persists them to `oof_scores.npy`; the simulator uses those. Corrected the profit maximum from $70,006 to $61,374. Row alignment is enforced at runtime — a misaligned score vector raises rather than silently producing plausible nonsense.

**Boundary optimum, undetectable.** The threshold grid started at 0.05 in 0.05 steps, and 0.05 won with profit still rising — indistinguishable from an unsearched region. The grid now spans 0.005–0.65 with 0.0025 resolution where the profit curve turns. The optimum at 0.0575 is a genuine interior maximum, and `boundary_optimum` is returned with every simulation so the case where it isn't can't pass silently.

**Straw-man baseline.** "Approve every application" is not a lending policy. Added `legacy_policy_baseline` — approve at credit score ≥ 600, ignoring installment count, merchant category and employment status. That omission is the risk-adjustment gap the project is about. Approve-all is retained as a labelled reference only.

**A commercially invalid recommendation.** The profit optimum declines 63% of the book. `build_strategy_ladder` now reports four strategies and recommends by a stated objective — *maximise approved volume subject to not losing money* — with a configurable volume floor. When the floor and profitability are incompatible, `volume_floor_feasible` says so rather than quietly recommending a loss.

**Hardcoded loss-given-default.** `* 0.65` appeared in three places, undocumented and unconfigurable, driving every loss figure. Now `settings.loss_given_default`, threaded through every function that computes a loss, adjustable per request, and returned with every response.

### Fixed — engineering defects

- `.env.example` documented in the README but never committed, for both backend and frontend. Added. This was the direct cause of "API unreachable" on first run.
- `optimization.py` used inline `__import__("numpy")` and exposed a `step` parameter that couldn't change the grid bounds.
- No test coverage of any financial logic.

### Added

**Backend** — `tests/` with 40 tests asserting hand-computed values (no test pins a headline figure); `pytest.ini`; out-of-fold scoring and persistence; `legacy_policy_baseline` and `approve_all_baseline`; `build_strategy_ladder`; `threshold_at_approval_rate`; `default_threshold_grid`; economic assumptions in `config.py`; `lgd`, `min_approval_rate_pct` and `credit_score_cutoff` query parameters; `caveats`, `assumptions`, `boundary_optimum`, `volume_floor_feasible` and `profit_floor` on every optimisation response.

**Frontend** — Executive summary rebuilt around the real baseline and loss attribution; new Risk analysis page with sort, filter and category drill-down; Strategy simulator rebuilt with live assumption controls; new Scenario comparison page; new Decision summary page; shared assumptions context so pages cannot disagree about what was assumed; `AssumptionControls` and `Caveats` components; `useOptimization` hook; regrouped navigation; landing page rewritten to match what the analysis actually found.

**Documentation** — `docs/NUMBERS.md` (the locked number set every document cites), project charter, PRD, personas, user stories, product backlog, roadmap, stakeholder register, RACI, and five dashboard screenshots.

### Changed

- `simulate_thresholds`, `portfolio_metrics` and `category_profitability` take `lgd` explicitly.
- `recommend_threshold` returns a strategy ladder; the old single-threshold signature is kept as a wrapper.
- `Strategy` responses carry `meets_volume_floor` — a property of the resulting approval rate, not of the rule that produced it.
- Simulation points gained `volume_retained_pct` and `approved_count`. Approving half the transactions is not retaining half the volume.
- `/app/optimization` moved to `/app/simulator`; the old path still resolves.

### Known limitations

Carried deliberately, documented rather than hidden — see [`docs/raci.md`](docs/raci.md) and the [risk register](docs/risk-register.md).

- LGD is assumed, not measured, and the headline figure is highly sensitive to it. At 45% the portfolio is already profitable and the problem dissolves.
- The volume floor was set unilaterally at 75%. It is a commercial negotiation, not an analytical output.
- UAT was executed by the person who wrote the software. That is verification, not user acceptance.
- The dataset is synthetic. Whether the risk-adjustment gap holds on real BNPL data is untested and untestable here.
- No independent model validation — the standard separation required in regulated lending is absent.

### Day 3 additions

**Governance** — [risk register](docs/risk-register.md) (9 risks, 4 of which materialised), [RAID log](docs/raid-log.md) (7 assumptions, 10 issues, 8 dependencies), [decision log](docs/decision-log.md) (6 decisions with options weighed and trade-offs accepted).

**Validation** — [UAT plan and execution record](docs/uat-plan.md): 10 cases run against the live API and a real browser, 10/10 after one failure and its root-cause investigation. Executable harness in `uat_run.py`. Two regression tests added for the `.env` defect, bringing the suite to 40.

**Narrative** — README rewritten as a product case study · [portfolio case study](docs/portfolio-case-study.md) · [retrospective](docs/retrospective.md) · [architecture](docs/architecture.md).

**QA** — `check_consistency.py` pulls canonical figures from the live API and scans every document for superseded values. It found four real drifts: a stale test count in four documents, two documents using a different loss-share denominator than the dashboard, and the project charter quoting a figure from the wrong scikit-learn version.

### Fixed — Day 3

- **`.env.example` shipped with `API_HOST` / `API_PORT`**, neither of which is a Settings field. Pydantic's default `extra="forbid"` turned a typo in an optional config file into a crash at import time, before any error handler existed to explain it. Corrected to real fields, `extra = "ignore"` added, two regression tests.
- **Comparison page contradicted itself** — highlighted a loss-making strategy as "best" while the recommendation star sat on a different, profitable column.
- **Loss-share denominator differed** between the dashboard (41.5%) and NUMBERS.md (41.9%). Denominator now stated explicitly and both figures published.

---

## Production incident — missing artifacts surfaced as a CORS error

**Symptom.** On Vercel, `/api/optimization/thresholds` returned 500 while `/api/profitability/merchants` returned 200. The browser reported `No 'Access-Control-Allow-Origin' header is present`, which pointed the investigation at CORS.

**Root cause.** `app/ml/oof_scores.npy` is gitignored, so it is absent from any deployment built from the repository. `get_oof_scores()` raised `FileNotFoundError`, which nothing handled. Endpoints that do not need that artifact were unaffected, which is why only one endpoint failed.

**Why it looked like CORS.** An unhandled exception propagates *past* `CORSMiddleware`, so the 500 Starlette generates above it carries no `Access-Control-Allow-Origin` header. The browser sees a header-less error response and reports a CORS violation — hiding the real fault. Demonstrated in `tests/test_error_handling.py`.

**Not the cause.** Query-string construction. `client.js` passes an axios `params` object, which serialises correctly; the 422 `float_parsing` error seen during manual testing came from ampersands being encoded in that hand-built URL, and is a different failure (422) from the one the browser hit (500).

**Fixed**
- `FileNotFoundError` handler returning a legible 503 that names the missing artifact.
- Catch-all `Exception` handler, so no error can reach a browser without CORS headers.
- New `GET /health/artifacts` — reports which artifacts are present and which endpoints are consequently available.
- CORS `allow_origins` narrowed from `["*"]` to an explicit list (`["*"]` with `allow_credentials=True` is invalid per the Fetch spec and was never working for credentialed requests).
- `.gitignore` annotated with the deployment consequence.
- 7 regression tests, bringing the suite to 47.
