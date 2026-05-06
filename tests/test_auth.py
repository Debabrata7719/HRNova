"""
Test 1 — Authentication
Tests: login success, wrong password, JWT token structure, role detection.
"""
import pytest


class TestAuthLogic:
    """Unit tests for auth.auth module — no HTTP, direct function calls."""

    def test_wrong_password_rejected(self, hr_employee):
        from auth.auth import login
        result = login(hr_employee["email"], "definitely_wrong_password_xyz")
        assert result["success"] is False
        assert result["user"] is None
        assert "password" in result["message"].lower() or "not found" in result["message"].lower()

    def test_nonexistent_email_rejected(self):
        from auth.auth import login
        result = login("nobody@nowhere.com", "anypassword")
        assert result["success"] is False
        assert result["user"] is None

    def test_empty_credentials_rejected(self):
        from auth.auth import login
        result = login("", "")
        assert result["success"] is False

    def test_jwt_token_structure(self, hr_token):
        """JWT must be a 3-part dot-separated string."""
        parts = hr_token.split(".")
        assert len(parts) == 3, "JWT must have header.payload.signature"

    def test_jwt_contains_correct_role(self, hr_token):
        from jose import jwt
        from src.config import get_settings
        s = get_settings()
        payload = jwt.decode(hr_token, s.SECRET_KEY, algorithms=[s.JWT_ALGORITHM])
        assert payload["role"] == "HR"

    def test_employee_jwt_role(self, employee_token):
        from jose import jwt
        from src.config import get_settings
        s = get_settings()
        payload = jwt.decode(employee_token, s.SECRET_KEY, algorithms=[s.JWT_ALGORITHM])
        assert payload["role"] == "EMPLOYEE"


class TestAuthAPI:
    """Integration tests for /api/auth/login endpoint."""

    def test_login_endpoint_wrong_password(self, api_client, hr_employee):
        resp = api_client.post(
            "/api/auth/login",
            json={"email": hr_employee["email"], "password": "wrong_password_xyz"},
        )
        assert resp.status_code == 401

    def test_login_endpoint_nonexistent_user(self, api_client):
        resp = api_client.post(
            "/api/auth/login",
            json={"email": "ghost@nowhere.com", "password": "anything"},
        )
        assert resp.status_code == 401

    def test_login_endpoint_missing_fields(self, api_client):
        resp = api_client.post("/api/auth/login", json={})
        assert resp.status_code == 422  # Pydantic validation error

    def test_protected_endpoint_without_token(self, api_client):
        """Accessing /api/leaves without token must return 403 (no bearer)."""
        resp = api_client.get("/api/leaves")
        assert resp.status_code in (401, 403)

    def test_protected_endpoint_with_invalid_token(self, api_client):
        resp = api_client.get(
            "/api/leaves",
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert resp.status_code == 401

    def test_hr_login_returns_token(self, hr_token):
        """hr_token fixture already validates this — just assert it's non-empty."""
        assert hr_token and len(hr_token) > 20

    def test_employee_login_returns_token(self, employee_token):
        assert employee_token and len(employee_token) > 20
