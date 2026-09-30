"""HTTP integration tests for authentication and protected user endpoints."""

from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from trade_ware.database.base import Base
from trade_ware.database.session import get_db
from trade_ware.main import app


@pytest.fixture
def client():
    """Provide a client backed by an isolated SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _register_and_verify(client: TestClient) -> dict:
    """Register and verify a test user, returning the login token pair."""
    with patch(
        "trade_ware.services.user_auth_service.EmailService.send_email"
    ):
        registration = client.post(
            "/api/v1/auth/register",
            json={
                "email": "person@example.com",
                "password": "StrongPass123!",
            },
        )
    assert registration.status_code == 201
    verification_url = registration.json()["verification_url"]
    token = parse_qs(urlparse(verification_url).query)["token"][0]
    verification = client.get(
        "/api/v1/auth/verify-email", params={"token": token}
    )
    assert verification.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "person@example.com",
            "password": "StrongPass123!",
        },
    )
    assert login.status_code == 200
    return login.json()


def test_protected_flow_supports_refresh_profile_and_account(client):
    """Verify the main authenticated HTTP flow and token rotation."""
    tokens = _register_and_verify(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    profile = client.get("/api/v1/users/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["profile_completed"] is False

    account = client.get(
        "/api/v1/users/me/paper-account", headers=headers
    )
    assert account.status_code == 200
    assert account.json()["cash_balance"] == "1000.00"

    update = client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={"first_name": "Ada", "last_name": "Lovelace"},
    )
    assert update.status_code == 200
    assert update.json()["profile_completed"] is True

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    replay = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert replay.status_code == 401


def test_protected_endpoint_requires_authentication(client):
    """Verify protected endpoints reject requests without a bearer token."""
    response = client.get("/api/v1/users/me/paper-account")

    assert response.status_code == 401
