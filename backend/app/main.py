import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import segmentation, profitability, risk, portfolio, optimization, explainability
from app.services.risk_model import ModelVersionMismatchError, ModelFileCorruptError

logger = logging.getLogger("bnpl")

app = FastAPI(
    title=settings.app_name,
    description="BNPL profitability & risk optimization analysis API",
    version="0.1.0",
)

# Explicit origins rather than "*".
#
# Note that ["*"] together with allow_credentials=True is invalid per the Fetch
# spec — browsers reject it — so the wildcard was never actually working for a
# credentialed request. Listing origins explicitly is both correct and required.
ALLOWED_ORIGINS = [
    "https://bnpl-app-taupe.vercel.app/",
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


@app.exception_handler(ModelVersionMismatchError)
async def model_version_mismatch_handler(request: Request, exc: ModelVersionMismatchError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "model_version_mismatch",
            "detail": str(exc),
        },
    )


@app.exception_handler(ModelFileCorruptError)
async def model_file_corrupt_handler(request: Request, exc: ModelFileCorruptError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "model_file_corrupt",
            "detail": str(exc),
        },
    )


@app.exception_handler(FileNotFoundError)
async def missing_artifact_handler(request: Request, exc: FileNotFoundError):
    """A required data or model artifact is not present on this deployment.

    This is the dominant production failure mode for this service, because the
    generated artifacts (CSVs, model, out-of-fold scores) are gitignored and so
    are absent from any deployment built straight from the repository.

    It is handled explicitly rather than left to propagate for a reason that is
    not obvious: an UNHANDLED exception escapes past CORSMiddleware, so the 500
    that Starlette generates above it carries no Access-Control-Allow-Origin
    header. The browser then reports a CORS error and hides the real cause. A
    registered handler produces a normal response that travels back out through
    CORSMiddleware and gets its headers, so the client sees the actual problem.
    """
    logger.error("Missing artifact: %s", exc)
    return JSONResponse(
        status_code=503,
        content={
            "error": "missing_artifact",
            "detail": str(exc),
            "hint": (
                "A required generated artifact is missing from this deployment. "
                "Check GET /health/artifacts to see which. These files are "
                "gitignored, so they must be committed explicitly or built "
                "during deployment."
            ),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Last resort, so that no error ever reaches a browser without CORS headers.

    Without this, any unexpected server-side exception surfaces in the browser
    as 'No Access-Control-Allow-Origin header is present' — which sends you
    debugging CORS instead of the actual fault.
    """
    logger.error("Unhandled error on %s: %s", request.url.path, exc)
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": f"{type(exc).__name__}: {exc}",
            "path": request.url.path,
        },
    )


app.include_router(segmentation.router)
app.include_router(profitability.router)
app.include_router(risk.router)
app.include_router(portfolio.router)
app.include_router(optimization.router)
app.include_router(explainability.router)


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


@app.get("/health/artifacts", tags=["Health"])
def health_artifacts():
    """Report which generated artifacts are present, and which endpoints need them.

    Exists because the failure it diagnoses is invisible from the outside: the
    app boots, /docs renders, and the endpoints that need no artifacts return
    200 — while the ones that do return 500. One request to this endpoint
    answers in a second what would otherwise be an afternoon of CORS debugging.
    """
    required = {
        "customers.csv": settings.customers_file,
        "transactions.csv": settings.transactions_file,
        "risk_model.pkl": settings.model_file,
        "feature_meta.json": settings.feature_meta_file,
        "oof_scores.npy": settings.oof_scores_file,
    }

    artifacts = {}
    for name, path in required.items():
        exists = path.exists()
        artifacts[name] = {
            "present": exists,
            "bytes": path.stat().st_size if exists else 0,
            "path": str(path),
        }

    def ok(*names):
        return all(artifacts[n]["present"] and artifacts[n]["bytes"] > 0 for n in names)

    endpoints = {
        "/api/profitability/merchants": ok("transactions.csv"),
        "/api/portfolio/profitability": ok("customers.csv", "transactions.csv"),
        "/api/segmentation/customers": ok("customers.csv", "transactions.csv"),
        "/api/risk/score": ok("risk_model.pkl", "feature_meta.json"),
        "/api/optimization/thresholds": ok(
            "customers.csv", "transactions.csv", "oof_scores.npy"
        ),
        "/api/explainability/{customer_id}": ok(
            "customers.csv", "transactions.csv", "risk_model.pkl"
        ),
    }

    missing = [n for n, a in artifacts.items() if not a["present"] or a["bytes"] == 0]
    return {
        "status": "ready" if not missing else "degraded",
        "missing": missing,
        "artifacts": artifacts,
        "endpoints_available": endpoints,
        "note": (
            "Generated artifacts are gitignored. A deployment built straight "
            "from the repository will not contain them."
        ),
    }