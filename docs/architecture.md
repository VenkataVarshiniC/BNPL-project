# Architecture

Two processes, no database, no queue, no cloud. The interesting part is not the topology — it is where the correctness guarantees sit.

---

## Data flow

```text
  generate_synthetic_data.py          [offline, seeded, run once]
        │  numpy default_rng(42)
        ▼
  customers.csv  ·  transactions.csv
        │
        ├──────────────────────────────┐
        ▼                              ▼
  train_model.py                  loader.py
   │  GradientBoosting             │  lru_cache
   │  + 5-fold CV                  │
   ▼                               │
  risk_model.pkl                   │
  oof_scores.npy  ◄────────────────┤   [the honest-simulation guarantee]
  feature_meta.json                │
        │                          │
        └────────────┬─────────────┘
                     ▼
            analytics_engine.py          [all financial logic — no ML]
             │  _economics()  ← the single revenue/loss/profit definition
             │  category_profitability()
             │  legacy_policy_baseline()  ·  approve_all_baseline()
             │  simulate_thresholds()     ← consumes OOF scores only
             │  build_strategy_ladder()   ← objective + volume floor
                     │
                     ▼
              FastAPI routers              [7 endpoints, read-only]
                     │  + assumptions, caveats, feasibility flags
                     ▼
              HTTP / JSON
                     │
                     ▼
            React + Vite console
             │  AssumptionsProvider  ← one assumption set for all pages
             │  useOptimization()
             ▼
   Executive · Risk · Simulator · Comparison · Decision
```

---

## Components

| Component | Responsibility | Why it is separate |
|---|---|---|
| `generate_synthetic_data.py` | Produce a seeded, statistically coherent portfolio | Offline and deterministic. Anyone can inspect exactly how the data was constructed — the alternative is an unauditable CSV. |
| `loader.py` | Cached DataFrame access | `lru_cache` keeps 42,000 rows in memory across requests. Isolating it means the CSV source could be replaced by a database without touching the analytics layer. |
| `train_model.py` | Fit the classifier **and** compute out-of-fold scores | OOF costs five full trainings. Doing it here rather than per request is what makes honest simulation affordable. |
| `risk_model.py` | Load model and OOF scores; score individual rows | Distinguishes a missing file, a torn write and a version mismatch, with a specific remedy for each. |
| **`analytics_engine.py`** | **All financial logic** | The load-bearing module. Contains no ML and no HTTP, so every number it produces is testable against hand-computed values. |
| `explainability.py` | SHAP attribution for a single score | Isolated because SHAP is slow and optional; nothing else depends on it. |
| `routers/` | HTTP surface, validation, assumption plumbing | Thin by design. No business logic lives here. |
| `state/assumptions.jsx` | Shared assumption set across pages | Above the page tree so the simulator and decision summary cannot disagree about what was assumed. |
| `useOptimization.js` | Fetch the simulation under current assumptions | One hook, so every projection on every screen comes from the same call shape. |

---

## Where the guarantees live

Four properties this product must not violate, and where each is enforced.

**1. Simulation never scores rows the model trained on.**
`train_model.py` computes 5-fold `cross_val_predict` and persists `oof_scores.npy`; `simulate_thresholds` accepts a score vector and raises if its length doesn't match the transaction frame. The guarantee is a runtime assertion, not a convention — because a misaligned vector produces plausible, meaningless results rather than an error.

**2. Category attribution reconciles to the portfolio.**
`_economics()` is the single definition of revenue, loss and profit; `category_profitability` and `portfolio_metrics` both call it. Asserted in `test_category_profits_sum_to_portfolio_profit` and again in [UAT-02](uat-plan.md).

**3. A projection cannot be returned without its assumptions.**
`OptimizationResponse` requires `assumptions` and `caveats`. They are not optional fields a caller might omit — the response model won't validate without them. A figure cannot be separated from its qualifications in transit.

**4. An optimum on the grid boundary is reported as such.**
`build_strategy_ladder` compares the winning threshold against the grid extremes and returns `boundary_optimum`. Without it, an unsearched region is indistinguishable from a located maximum.

---

## Technology choices and trade-offs

| Choice | Alternative | Why | Cost |
|---|---|---|---|
| **CSV + in-memory pandas** | PostgreSQL | 42,000 rows fit comfortably in memory. A database would add deployment surface and migrations to a read-only analytical workload. | No concurrent writes, no persistence beyond regeneration. Fine — there are none. |
| **Gradient boosting** | Logistic regression / XGBoost | Captures the non-linear interactions the generator encodes; scikit-learn ships it, no extra dependency. | AUC 0.708 is modest, but model choice is not the binding constraint here — the economics are. See the [backlog](product-backlog.md#forward-backlog--not-built). |
| **Persisted OOF scores** | Compute per request | Five trainings per request would make the simulator unusable. | The file must be regenerated whenever data or model changes. Enforced by both living in `train_model.py`. |
| **FastAPI** | Flask / Django | Pydantic response models make "assumptions and caveats are required" a schema guarantee rather than a habit. Automatic OpenAPI docs. | Async machinery this workload doesn't need. |
| **React + Vite** | Streamlit / Dash | Precise control over how uncertainty is presented — which is most of the product's value. Streamlit would have been faster to build and would have made "report the trade-off, not an optimum" much harder to express. | More code. 787 KB bundle, unsplit. |
| **React Context for assumptions** | Redux / Zustand | Three values, one writer. A store would be ceremony. | Every consumer re-renders on change. Immaterial at this scale. |
| **Recharts** | D3 / Plotly | Declarative, composable with the component model, small enough. | Less control than raw D3 for anything unusual. |
| **No authentication** | Auth0 / JWT | Single-user local analysis tool with no real data and no write path. Auth would be theatre. | Not deployable as-is to a shared environment. Deliberate — see the [charter](project-charter.md#4-scope). |

**Deliberately not introduced:** message queue, cache layer, container orchestration, feature store, model registry, workflow scheduler. Each would be defensible in a production system and none would improve a three-day decision-support prototype. The architecture is shaped by what the product must guarantee, not by what a production system usually contains.

---

## API surface

All read-only. There is no write path to any approval system — see [DEC-05](decision-log.md#dec-05).

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/portfolio/profitability` | Portfolio aggregate with the LGD assumption attached |
| `GET` | `/api/profitability/merchants` | Per-category economics, reconciling to the portfolio |
| `GET` | `/api/segmentation/customers` | Four RFM-style segments |
| `POST` | `/api/risk/score` | Default probability, risk tier, advisory action |
| `GET` | `/api/explainability/{customer_id}` | SHAP base value and ranked contributions |
| `GET` | `/api/optimization/thresholds` | Simulation, strategy ladder, both baselines, assumptions, caveats, feasibility flags |
| `GET` | `/health` · `/` | Liveness and endpoint index |

`/api/optimization/thresholds` accepts `lgd`, `min_approval_rate_pct` and `credit_score_cutoff`, and recomputes everything downstream. It is the only endpoint that matters for the product's central claim, and the only one carrying the full assumption and caveat payload.

---

## Failure modes handled

| Condition | Response | Why it is explicit |
|---|---|---|
| Model file absent | `FileNotFoundError` naming the command to run | The commonest first-run failure |
| Model file 0 bytes | HTTP 503 explaining a torn write and how to prevent it | Caused by `uvicorn --reload` restarting mid-write during training — non-obvious and easy to hit |
| Model file truncated | HTTP 503 with delete-and-retrain instructions | Same cause, different symptom |
| scikit-learn version mismatch | HTTP 503 naming the installed version and the fix | Pickled estimators are not portable across versions |
| OOF scores absent | `FileNotFoundError` pointing at `train_model.py` | Added with OOF scoring; the simulator is useless without them |
| Score vector misaligned | `ValueError` at the call site | The dangerous one — it would otherwise produce plausible nonsense |
| Unknown key in `.env` | Ignored | A typo in an optional config file should not crash the app before any handler exists to explain it |
| Backend unreachable | Frontend error state with retry | Two-process local setup; the backend terminal dies more often than anything else |

---

## Reproducing the whole pipeline

```bash
cd backend
pip install -r requirements.txt
python -m app.data.generate_synthetic_data   # seeded, deterministic
python -m app.ml.train_model                 # model + 5-fold OOF scores
python -m pytest -q                          # 40 tests
uvicorn app.main:app --port 8000

cd ../frontend
npm install && npm run dev
```

Verified clean-room: extracted into an empty directory, every step run from scratch, figures identical to [NUMBERS.md](NUMBERS.md).
