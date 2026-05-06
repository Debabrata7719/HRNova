"""
Test 4 & 9 — API Endpoints
Tests: leaves, memory, chat endpoints via FastAPI TestClient.
"""
import pytest


class TestLeavesAPI:
    """Test /api/leaves endpoints — requires HR token."""

    def test_get_leaves_requires_auth(self, api_client):
        resp = api_client.get("/api/leaves")
        assert resp.status_code in (401, 403)

    def test_get_leaves_employee_forbidden(self, api_client, employee_token):
        resp = api_client.get(
            "/api/leaves",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert resp.status_code == 403

    def test_get_leaves_hr_success(self, api_client, hr_token):
        resp = api_client.get(
            "/api/leaves",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_leave_stats_hr(self, api_client, hr_token):
        resp = api_client.get(
            "/api/leaves/stats",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data

    def test_get_leave_stats_employee_forbidden(self, api_client, employee_token):
        resp = api_client.get(
            "/api/leaves/stats",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert resp.status_code == 403

    def test_approve_nonexistent_leave(self, api_client, hr_token):
        resp = api_client.put(
            "/api/leaves/999999/approve",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 404

    def test_reject_nonexistent_leave(self, api_client, hr_token):
        resp = api_client.put(
            "/api/leaves/999999/reject",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 404


class TestMemoryAPI:
    """Test /api/memory endpoints."""

    def test_get_memory_stats_authenticated(self, api_client, hr_token):
        resp = api_client.get(
            "/api/memory/stats",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        assert "total_memories" in resp.json()

    def test_get_memory_stats_requires_auth(self, api_client):
        resp = api_client.get("/api/memory/stats")
        assert resp.status_code in (401, 403)

    def test_get_user_memories(self, api_client, hr_token):
        resp = api_client.get(
            "/api/memory/user",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "memories" in data
        assert "total_memories" in data

    def test_get_all_users_memories_hr(self, api_client, hr_token):
        resp = api_client.get(
            "/api/memory/all",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_memories" in data
        assert "memories_by_user" in data

    def test_get_all_users_memories_employee_forbidden(self, api_client, employee_token):
        resp = api_client.get(
            "/api/memory/all",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert resp.status_code == 403

    def test_memory_cleanup_employee_forbidden(self, api_client, employee_token):
        resp = api_client.post(
            "/api/memory/cleanup",
            json={"days": 30},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert resp.status_code == 403

    def test_memory_cleanup_hr_success(self, api_client, hr_token):
        resp = api_client.post(
            "/api/memory/cleanup",
            json={"days": 365},  # Only deletes year-old memories — safe
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "deleted" in data
        assert "memories_before" in data


class TestChatAPI:
    """Test /api/chat endpoint."""

    def test_chat_requires_auth(self, api_client):
        resp = api_client.post(
            "/api/chat",
            json={"message": "hello", "session_id": "test-session"},
        )
        assert resp.status_code in (401, 403)

    def test_chat_missing_fields(self, api_client, hr_token):
        resp = api_client.post(
            "/api/chat",
            json={"message": "hello"},  # missing session_id
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 422

    def test_chat_returns_response(self, api_client, hr_token):
        """Send a simple greeting — should get a response back."""
        resp = api_client.post(
            "/api/chat",
            json={"message": "hello", "session_id": "pytest-session-001"},
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert len(data["response"]) > 0
        assert "session_id" in data

    def test_chat_session_get(self, api_client, hr_token):
        # First create a session
        api_client.post(
            "/api/chat",
            json={"message": "hello", "session_id": "pytest-session-002"},
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        # Then get it
        resp = api_client.get(
            "/api/chat/session/pytest-session-002",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is True

    def test_chat_session_delete(self, api_client, hr_token):
        # Create session
        api_client.post(
            "/api/chat",
            json={"message": "hello", "session_id": "pytest-session-003"},
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        # Delete it
        resp = api_client.delete(
            "/api/chat/session/pytest-session-003",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200

    def test_nonexistent_session_returns_not_exists(self, api_client, hr_token):
        resp = api_client.get(
            "/api/chat/session/nonexistent-session-xyz-99999",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["exists"] is False


class TestHealthEndpoints:
    """Test root and health endpoints."""

    def test_root_endpoint(self, api_client):
        resp = api_client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_endpoint(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
