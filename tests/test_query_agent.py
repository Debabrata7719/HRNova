"""
Test 6 — Policy Q&A and Leave Balance Queries
Tests: ChromaDB policy search, leave balance formatting, leave status.
"""
import pytest


class TestPolicySearch:
    """Tests for ChromaDB policy retrieval."""

    def test_policy_chunks_returned(self):
        from src.main_agent.agents.query.executor import query_policy_chunks
        chunks = query_policy_chunks("casual leave policy", k=2)
        assert isinstance(chunks, list)
        assert len(chunks) >= 1, (
            "No policy chunks returned — run: python src/tools/embed_policy.py"
        )

    def test_policy_chunks_are_strings(self):
        from src.main_agent.agents.query.executor import query_policy_chunks
        chunks = query_policy_chunks("leave policy", k=3)
        for chunk in chunks:
            assert isinstance(chunk, str)
            assert len(chunk) > 0

    def test_different_queries_return_results(self):
        from src.main_agent.agents.query.executor import query_policy_chunks
        queries = [
            "casual leave",
            "sick leave",
            "earned leave",
            "notice period",
        ]
        for query in queries:
            chunks = query_policy_chunks(query, k=1)
            assert len(chunks) >= 1, f"No chunks for query: '{query}'"


class TestLeaveBalanceFormatting:
    """Unit tests for balance/status formatting functions."""

    def test_format_balance_response(self):
        from src.main_agent.agents.query.executor import format_balance_response
        balance = {
            "EL": {"used": 5, "allowed": 18, "remaining": 13},
            "CL": {"used": 2, "allowed": 12, "remaining": 10},
            "SL": {"used": 0, "allowed": 12, "remaining": 12},
        }
        response = format_balance_response(balance)
        assert "EL" in response
        assert "CL" in response
        assert "SL" in response
        assert "13" in response  # EL remaining
        assert "10" in response  # CL remaining

    def test_format_status_response_empty(self):
        from src.main_agent.agents.query.executor import format_status_response
        response = format_status_response([])
        assert "no leave" in response.lower() or "no request" in response.lower()

    def test_format_status_response_with_leaves(self):
        from src.main_agent.agents.query.executor import format_status_response
        leaves = [
            {
                "start_date": "2026-05-10",
                "end_date": "2026-05-12",
                "leave_type": "CL",
                "days": 3,
                "status": "pending",
                "reason": "personal work",
                "submitted_at": "2026-05-06 10:00:00",
            }
        ]
        response = format_status_response(leaves)
        assert "CL" in response
        assert "pending" in response.upper() or "PENDING" in response


class TestLeaveBalanceQuery:
    """Integration tests — requires MySQL."""

    def test_get_employee_balance(self, employee_employee):
        from src.main_agent.agents.query.executor import get_employee_balance
        balance = get_employee_balance(employee_employee["id"])
        assert "EL" in balance
        assert "CL" in balance
        assert "SL" in balance

    def test_get_leave_status(self, employee_employee):
        from src.main_agent.agents.query.executor import get_leave_status
        leaves = get_leave_status(employee_employee["id"])
        assert isinstance(leaves, list)
        # Each leave should have required fields
        for leave in leaves:
            assert "leave_type" in leave
            assert "status" in leave
            assert "start_date" in leave
