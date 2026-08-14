from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_pr_build_job_is_secretless():
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    preview_job = workflow.split("  Production-Build-And-Verify:", 1)[0]

    assert "secrets." not in preview_job
    assert "SUPABASE_SERVICE_ROLE_KEY" not in preview_job
    assert "vercel pull" not in preview_job
    assert "vercel build" not in preview_job


def test_privileged_reusable_workflow_is_immutable():
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "weekly-repo-research.yml").read_text(
        encoding="utf-8"
    )

    assert "reusable-weekly-repo-research.yml@main" not in workflow
    assert "reusable-weekly-repo-research.yml@12067d726107329744846c6d33c8f423d78a87e9" in workflow


def test_cross_origin_api_requests_are_not_allowed_from_arbitrary_sites():
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers.get("access-control-allow-origin") is None


def test_local_vite_origin_remains_allowed_for_development():
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
