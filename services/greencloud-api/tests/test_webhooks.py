import hashlib
import hmac
import json

from app.config import settings


def _sign_payload(payload: bytes, secret: str) -> str:
    """Generate a valid GitHub webhook signature."""
    sig = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={sig}"


SAMPLE_PUSH_PAYLOAD = {
    "ref": "refs/heads/main",
    "after": "abc1234567890def1234567890abc1234567890ab",
    "repository": {
        "clone_url": "https://github.com/mattygibson/green-cloud.git",
        "full_name": "mattygibson/green-cloud",
    },
    "pusher": {"name": "mattygibson"},
}


def test_webhook_rejects_missing_signature(client):
    """Webhook should return 401 without a signature."""
    response = client.post(
        "/webhooks/github",
        json=SAMPLE_PUSH_PAYLOAD,
        headers={"X-GitHub-Event": "push"},
    )
    assert response.status_code == 401


def test_webhook_rejects_invalid_signature(client):
    """Webhook should return 401 with an invalid signature."""
    response = client.post(
        "/webhooks/github",
        json=SAMPLE_PUSH_PAYLOAD,
        headers={
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": "sha256=invalid",
        },
    )
    assert response.status_code == 401


def test_webhook_accepts_valid_push(client):
    """Webhook should accept a valid push to main."""
    payload = json.dumps(SAMPLE_PUSH_PAYLOAD).encode()
    signature = _sign_payload(payload, settings.github_webhook_secret)

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": signature,
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["environment"] == "prod"
    assert data["status"] == "pending"
    assert data["branch"] == "main"


def test_webhook_ignores_non_push_events(client):
    """Webhook should ignore non-push events."""
    payload = json.dumps(SAMPLE_PUSH_PAYLOAD).encode()
    signature = _sign_payload(payload, settings.github_webhook_secret)

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": signature,
        },
    )
    # Should return 200 (not an error, just ignored)
    assert response.status_code == 200
