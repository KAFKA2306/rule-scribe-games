from scripts.vercel_deployment_budget import BudgetDecision, decide_budget, latest_ready_production_sha
from scripts.verify_vercel_git_deployment import DeploymentMatch, find_deployment_for_sha


def test_finds_exact_ready_production_sha():
    payload = {
        "deployments": [
            {
                "uid": "dpl_new",
                "url": "example-new.vercel.app",
                "state": "READY",
                "target": "production",
                "meta": {"githubCommitSha": "abc123"},
            },
            {
                "uid": "dpl_old",
                "url": "example-old.vercel.app",
                "state": "READY",
                "target": "production",
                "meta": {"githubCommitSha": "older"},
            },
        ]
    }

    assert find_deployment_for_sha(payload, "abc123") == DeploymentMatch(
        deployment_id="dpl_new",
        url="example-new.vercel.app",
        state="READY",
        commit_sha="abc123",
    )


def test_does_not_treat_different_sha_as_current_production():
    payload = {
        "deployments": [
            {
                "uid": "dpl_old",
                "state": "READY",
                "target": "production",
                "meta": {"githubCommitSha": "older"},
            }
        ]
    }
    assert find_deployment_for_sha(payload, "expected") is None


def test_ignores_preview_for_same_sha():
    payload = {
        "deployments": [
            {
                "uid": "dpl_preview",
                "state": "READY",
                "target": "preview",
                "meta": {"githubCommitSha": "abc123"},
            }
        ]
    }
    assert find_deployment_for_sha(payload, "abc123") is None


def test_preserves_terminal_failure_state_for_caller():
    payload = {
        "deployments": [
            {
                "uid": "dpl_error",
                "state": "ERROR",
                "target": "production",
                "meta": {"githubCommitSha": "abc123"},
            }
        ]
    }
    match = find_deployment_for_sha(payload, "abc123")
    assert match is not None
    assert match.state == "ERROR"


def test_missing_meta_is_not_inferred_from_position():
    payload = {"deployments": [{"uid": "dpl_latest", "state": "READY", "target": "production", "meta": {}}]}
    assert find_deployment_for_sha(payload, "abc123") is None


def _production_payload(sha: str = "older"):
    return {
        "deployments": [
            {
                "uid": "dpl_prod",
                "state": "READY",
                "target": "production",
                "meta": {"githubCommitSha": sha},
            }
        ]
    }


def test_budget_is_current_when_latest_production_matches_main():
    decision = decide_budget(
        team_payload={"deployments": [{}] * 100},
        project_payload=_production_payload("abc123"),
        expected_sha="abc123",
    )
    assert decision.state == "current"
    assert decision.latest_production_sha == "abc123"


def test_budget_is_quota_saturated_at_observed_free_limit():
    decision = decide_budget(
        team_payload={"deployments": [{}] * 100},
        project_payload=_production_payload("older"),
        expected_sha="abc123",
    )
    assert decision == BudgetDecision(
        state="quota_saturated",
        deployment_count=100,
        latest_production_sha="older",
        reason="at least 100 team deployments were observed in the last 24 hours",
    )


def test_budget_is_deployable_below_limit_when_production_is_behind():
    decision = decide_budget(
        team_payload={"deployments": [{}] * 42},
        project_payload=_production_payload("older"),
        expected_sha="abc123",
    )
    assert decision.state == "deployable"
    assert decision.deployment_count == 42


def test_latest_ready_sha_ignores_error_and_preview_deployments():
    payload = {
        "deployments": [
            {"state": "ERROR", "target": "production", "meta": {"githubCommitSha": "bad"}},
            {"state": "READY", "target": "preview", "meta": {"githubCommitSha": "preview"}},
            {"state": "READY", "target": "production", "meta": {"githubCommitSha": "good"}},
        ]
    }
    assert latest_ready_production_sha(payload) == "good"
