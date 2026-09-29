import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from trade_ware.database.base import Base
from trade_ware.database.session import get_db
from trade_ware.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tradeware.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def override_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


def test_register_user_creates_unverified_record():
    payload = {
        "email": "newuser@example.com",
        "password": "StrongPass123!",
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["is_verified"] is False
    assert "verification_url" in body


def test_register_rejects_duplicate_email():
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPass123!",
    }

    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201, first.text

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "Email already registered"
