from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import (
    segmentation,
    profitability,
    risk,
    portfolio,
    optimization,
    explainability,
)
from app.services.risk_model import (
    ModelVersionMismatchError,
    ModelFileCorruptError,
)

app = FastAPI(
    title=settings.app_name,
    description="BNPL profitability & risk optimization analysis API",
    version="0.1.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

# Frontend URLs allowed to communicate with this backend.
ALLOWED_ORIGINS = [
    "https://bnpl-app-flame.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODEL ERROR HANDLERS
# ============================================================

@app.exception_handler(ModelVersionMismatchError)
async def model_version_mismatch_handler(
    request: Request,
    exc: ModelVersionMismatchError,
):
    return JSONResponse(
        status_code=503,
        content={
            "error": "model_version_mismatch",
            "detail": str(exc),
        },
    )


@app.exception_handler(ModelFileCorruptError)
async def model_file_corrupt_handler(
    request: Request,
    exc: ModelFileCorruptError,
):
    return JSONResponse(
        status_code=503,
        content={
            "error": "model_file_corrupt",
            "detail": str(exc),
        },
    )


# ============================================================
# ROUTERS
# ============================================================

app.include_router(segmentation.router)
app.include_router(profitability.router)
app.include_router(risk.router)
app.include_router(portfolio.router)
app.include_router(optimization.router)
app.include_router(explainability.router)


# ============================================================
# HEALTH / ROOT ENDPOINTS
# ============================================================

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "app": settings.app_name,
        "endpoints": [
            "/api/segmentation/customers",
            "/api/profitability/merchants",
            "/api/risk/score",
            "/api/portfolio/profitability",
            "/api/optimization/thresholds",
            "/api/explainability/{customer_id}",
        ],
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
