"""
Shared pytest fixtures for NovaHR test suite.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def db():
    """Real DB connection — used for integration tests that need MySQL."""
    from src.tools.db_connection import get_db
    return get_db()


@pytest.fixture(scope="session")
def hr_employee(db):
    """Return the first HR employee from the DB."""
    result = db.execute_query(
        "SELECT id, name, email, auth_role FROM employees WHERE auth_role = 'HR' LIMIT 1"
    )
    assert result, "No HR employee found in DB — run auth/setup_auth.py first"
    return result[0]


@pytest.fixture(scope="session")
def employee_employee(db):
    """Return the first EMPLOYEE-role user from the DB."""
    result = db.execute_query(
        "SELECT id, name, email, auth_role FROM employees WHERE auth_role = 'EMPLOYEE' LIMIT 1"
    )
    assert result, "No EMPLOYEE found in DB — add one via scripts/add_employee.py"
    return result[0]


@pytest.fixture(scope="session")
def api_client():
    """FastAPI TestClient — no live server needed."""
    from api.main import app
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture(scope="session")
def hr_token(api_client, hr_employee):
    """
    Get a valid JWT token for the HR user.
    Tries common passwords; skips if none work.
    """
    common_passwords = ["721242", "123456", "admin", "password", "novahr", "123"]
    for pwd in common_passwords:
        resp = api_client.post(
            "/api/auth/login",
            json={"email": hr_employee["email"], "password": pwd},
        )
        if resp.status_code == 200 and resp.json().get("token"):
            return resp.json()["token"]
    pytest.skip(
        f"Could not authenticate HR user {hr_employee['email']} — "
        "reset password via: python scripts/add_employee.py (option 2)"
    )


@pytest.fixture(scope="session")
def employee_token(api_client, employee_employee):
    """Get a valid JWT token for the Employee user."""
    common_passwords = ["123", "721242", "123456", "admin", "password", "novahr"]
    for pwd in common_passwords:
        resp = api_client.post(
            "/api/auth/login",
            json={"email": employee_employee["email"], "password": pwd},
        )
        if resp.status_code == 200 and resp.json().get("token"):
            return resp.json()["token"]
    pytest.skip(
        f"Could not authenticate Employee user {employee_employee['email']} — "
        "reset password via: python scripts/add_employee.py (option 2)"
    )


@pytest.fixture
def base_state():
    """Minimal valid LangGraph state dict for router/agent tests."""
    return {
        "input": "",
        "step": "initial",
        "intent": "",
        "role": "HR",
        "leave_data": {},
        "email_data": {},
        "schedule_data": {},
        "output": "",
        "employee_id": 1,
        "employee_name": "Debabrata Dey",
        "schedule_title": "",
        "schedule_date": "",
        "schedule_time": "",
        "schedule_description": "",
        "leave_agent_memory": {},
        "email_agent_memory": {},
        "general_agent_memory": {},
        "query_agent_memory": {},
        "schedule_agent_memory": {},
        "long_term_memory": [],
        "session_summaries": {},
    }
