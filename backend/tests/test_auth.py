"""Integration tests for Auth and RBAC — Task 27.

Uses FastAPI TestClient against the real app with PostgreSQL.
Tests cover exactly the 8 required scenarios from the spec:

27.2:
  - POST /auth/login valid credentials → 200
  - POST /auth/login wrong password → 401 with generic message
  - POST /auth/login missing required fields → 422

27.3:
  - Protected endpoint, no token → 401
  - Protected endpoint, expired JWT → 401
  - Protected endpoint, wrong role → 403
  - Protected endpoint, correct role → 200
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.auth.hashing import hash_password
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User

client = TestClient(app, raise_server_exceptions=False)

# ── Test user credentials ─────────────────────────────────────────────────────

_ADMIN_EMAIL = f"t27admin_{uuid.uuid4().hex[:6]}@test.com"
_ADMIN_PASS = "T27Admin!Pass"
_EMP_EMAIL = f"t27emp_{uuid.uuid4().hex[:6]}@test.com"
_EMP_PASS = "T27Emp!Pass"

_user_ids: list[str] = []


@pytest.fixture(scope="module", autouse=True)
def seed_users():
    """Create test users before the module; clean up after."""
    db = SessionLocal()
    try:
        for email, password, role in [
            (_ADMIN_EMAIL, _ADMIN_PASS, "admin"),
            (_EMP_EMAIL, _EMP_PASS, "employee"),
        ]:
            u = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=hash_password(password),
                role=role,
                is_active=True,
                must_change_password=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                registration_status="ACTIVE",
                email_verified=False,
            )
            db.add(u)
            _user_ids.append(str(u.id))
        db.commit()
    finally:
        db.close()

    yield

    db2 = SessionLocal()
    try:
        from sqlalchemy import text
        for uid in _user_ids:
            db2.execute(text(f"DELETE FROM audit_logs WHERE actor_id='{uid}'"))
            db2.execute(text(f"DELETE FROM users WHERE id='{uid}'"))
        db2.commit()
    finally:
        db2.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _login(email: str, password: str):
    return client.post("/auth/login", json={"email": email, "password": password})


def _admin_token() -> str:
    return _login(_ADMIN_EMAIL, _ADMIN_PASS).json()["access_token"]


def _emp_token() -> str:
    return _login(_EMP_EMAIL, _EMP_PASS).json()["access_token"]


def _expired_token() -> str:
    """Syntactically valid JWT that expired 1 hour ago."""
    payload = {
        "sub": str(uuid.uuid4()),
        "role": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── 27.2: POST /auth/login ────────────────────────────────────────────────────

def test_login_valid_credentials_returns_200():
    """Valid credentials → 200 with access_token, token_type, role, must_change_password."""
    r = _login(_ADMIN_EMAIL, _ADMIN_PASS)
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data and len(data["access_token"]) > 20
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert "must_change_password" in data


def test_login_wrong_password_returns_401_generic_message():
    """Wrong password → 401. Message must not reveal which field (email vs password) failed."""
    r = _login(_ADMIN_EMAIL, "CompletelyWrongPass!")
    assert r.status_code == 401
    detail = r.json().get("detail", "").lower()
    # The message should be generic — it may mention both "email" and "password"
    # together (e.g. "Invalid email or password") but must NOT say something like
    # "password incorrect" or "email not found" that reveals which field failed.
    assert len(detail) > 0, "401 response must include a detail message"
    # Neither field should be called out alone
    assert not ("password" in detail and "email" not in detail), \
        "Message must not single out 'password' — must be generic"
    assert not ("email" in detail and "password" not in detail), \
        "Message must not single out 'email' — must be generic"


def test_login_missing_email_returns_422():
    """Missing email field → 422 Unprocessable Entity (Pydantic validation)."""
    r = client.post("/auth/login", json={"password": _ADMIN_PASS})
    assert r.status_code == 422


def test_login_missing_password_returns_422():
    """Missing password field → 422."""
    r = client.post("/auth/login", json={"email": _ADMIN_EMAIL})
    assert r.status_code == 422


# ── 27.3: Protected endpoint authorization ────────────────────────────────────

def test_protected_no_token_returns_401():
    """No Authorization header on protected endpoint → 401."""
    r = client.get("/users")
    assert r.status_code == 401


def test_protected_expired_token_returns_401():
    """Expired JWT → 401."""
    r = client.get("/users", headers={"Authorization": f"Bearer {_expired_token()}"})
    assert r.status_code == 401


def test_protected_wrong_role_returns_403():
    """Employee token on admin-only endpoint → 403."""
    tok = _emp_token()
    r = client.get("/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_protected_correct_role_returns_200():
    """Admin token on admin-only endpoint → 200."""
    tok = _admin_token()
    r = client.get("/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
