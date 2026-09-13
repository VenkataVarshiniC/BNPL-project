# BNPL Profitability & Risk Optimization API — Backend

FastAPI service powering the BNPL profitability and risk optimization analysis.

## Setup

```bash
python -m venv venv && source venv/bin/activate   # optional
pip install -r requirements.txt
```

## 1. Generate synthetic data (5,000 customers / 42,000 transactions)

```bash
python -m app.data.generate_synthetic_data
```

## 2. Train the default-risk model

```bash
python -m app.ml.train_model
```

## 3. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/docs

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/segmentation/customers` | Customer segmentation (RFM-style) |
| GET | `/api/profitability/merchants` | Merchant/category profitability |
| POST | `/api/risk/score` | Default risk score for a proposed transaction |
| GET | `/api/portfolio/profitability` | Portfolio-level net profit |
| GET | `/api/optimization/thresholds` | Approval-threshold profit simulation |
| GET | `/api/explainability/{customer_id}` | SHAP explanation for a risk score |

## Folder structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app + router wiring
│   ├── config.py                # settings (paths, dataset size, seed)
│   ├── models/schemas.py        # Pydantic request/response models
│   ├── data/
│   │   ├── generate_synthetic_data.py
│   │   ├── loader.py            # cached CSV -> DataFrame loading
│   │   ├── customers.csv        # generated
│   │   └── transactions.csv     # generated
│   ├── ml/
│   │   ├── train_model.py       # trains + persists GradientBoosting model
│   │   ├── risk_model.pkl       # generated
│   │   └── feature_meta.json    # generated
│   ├── services/
│   │   ├── analytics_engine.py  # segmentation, profitability, optimization math
│   │   ├── risk_model.py        # model loading + scoring
│   │   └── explainability.py    # SHAP explanations
│   └── routers/                 # one file per endpoint group
├── requirements.txt
└── .env.example
```
