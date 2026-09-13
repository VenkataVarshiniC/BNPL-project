"""Error-response contract tests.

Regression cover for a production incident: `/api/optimization/thresholds`
returned 500 on Vercel while `/api/profitability/merchants` returned 200. The
cause was a missing gitignored artifact (`oof_scores.npy`), but the browser
reported it as a CORS error, because an UNHANDLED exception escapes past
CORSMiddleware and the resulting 500 carries no Access-Control-Allow-Origin
header. The real fault was invisible from the client.

These tests assert the two properties that keep that from recurring:
  1. A missing artifact returns a legible 503, not an opaque 500.
  2. No error response ever reaches a browser without CORS headers.
"""
import shutil

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

ORIGIN = {"Origin": "https://bnpl-app-flame.vercel.app"}


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def missing_oof_scores(tmp_path):
    """Temporarily remove the out-of-fold scores, as a deployment would lack them."""
    src = settings.oof_scores_file
    if not src.exists():
        pytest.skip("oof_scores.npy not generated; run train_model first")
    backup = tmp_path / "oof_scores.npy"
    shutil.move(str(src), str(backup))
    try:
        from app.services.risk_model import get_oof_scores
        get_oof_scores.cache_clear()
        yield
    finally:
        shutil.move(str(backup), str(src))
        from app.services.risk_model import get_oof_scores
        get_oof_scores.cache_clear()


def test_missing_artifact_returns_503_not_500(client, missing_oof_scores):
    r = client.get("/api/optimization/thresholds", headers=ORIGIN)
    assert r.status_code == 503
    assert r.json()["error"] == "missing_artifact"
    assert "oof_scores" in r.json()["detail"]


def test_missing_artifact_error_still_carries_cors_headers(client, missing_oof_scores):
    """The property that makes the failure debuggable from a browser at all."""
    r = client.get("/api/optimization/thresholds", headers=ORIGIN)
    assert r.headers.get("access-control-allow-origin") == ORIGIN["Origin"]


def test_endpoints_without_that_artifact_keep_working(client, missing_oof_scores):
    """A missing artifact must degrade one endpoint, not the whole service."""
    assert client.get("/api/profitability/merchants", headers=ORIGIN).status_code == 200
    assert client.get("/health", headers=ORIGIN).status_code == 200


def test_artifact_health_reports_what_is_missing(client, missing_oof_scores):
    d = client.get("/health/artifacts", headers=ORIGIN).json()
    assert d["status"] == "degraded"
    assert "oof_scores.npy" in d["missing"]
    assert d["endpoints_available"]["/api/optimization/thresholds"] is False
    assert d["endpoints_available"]["/api/profitability/merchants"] is True


def test_artifact_health_reports_ready_when_complete(client):
    d = client.get("/health/artifacts", headers=ORIGIN).json()
    assert d["status"] == "ready"
    assert d["missing"] == []
    assert all(d["endpoints_available"].values())


def test_query_params_are_parsed_as_separate_values(client):
    """Guards the hypothesis that was investigated and ruled out.

    If a client ever collapsed the query string into a single `lgd` value,
    FastAPI would return 422 with a float_parsing error. Correctly separated
    params must return 200 and echo the values back in `assumptions`.
    """
    r = client.get(
        "/api/optimization/thresholds",
        params={"lgd": 0.45, "min_approval_rate_pct": 60, "credit_score_cutoff": 640},
        headers=ORIGIN,
    )
    assert r.status_code == 200
    a = r.json()["assumptions"]
    assert a["loss_given_default"] == 0.45
    assert a["min_approval_rate_pct"] == 60
    assert a["legacy_credit_score_cutoff"] == 640


def test_malformed_single_param_is_a_422_not_a_500(client):
    """The error the user saw when testing by hand was 422, not the browser's 500.

    Distinguishing these two is what separates a client-side query-construction
    bug from a server-side artifact problem.
    """
    r = client.get(
        "/api/optimization/thresholds",
        params={"lgd": "0.65&min_approval_rate_pct=75&credit_score_cutoff=600"},
        headers=ORIGIN,
    )
    assert r.status_code == 422
    assert r.json()["detail"][0]["type"] == "float_parsing"
