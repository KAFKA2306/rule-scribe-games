import pytest

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
