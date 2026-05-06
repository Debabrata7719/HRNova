"""
Test 3 — Leave Agent
Tests: date parsing, balance queries, leave submission workflow.
"""
import pytest
from datetime import datetime, timedelta


class TestDateParsing:
    """Unit tests for parse_date() — no DB needed."""

    def setup_method(self):
        from src.main_agent.agents.leave.executor import parse_date, calculate_days
        self.parse_date = parse_date
        self.calculate_days = calculate_days

    def test_today(self):
        result = self.parse_date("today")
        assert result == datetime.now().strftime("%Y-%m-%d")

    def test_tomorrow(self):
        result = self.parse_date("tomorrow")
        expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected

    def test_iso_format_no_swap(self):
        """Critical: 2026-05-10 must NOT become 2026-10-05."""
        assert self.parse_date("2026-05-10") == "2026-05-10"
        assert self.parse_date("2026-01-15") == "2026-01-15"
        assert self.parse_date("2026-12-01") == "2026-12-01"

    def test_month_name_format(self):
        assert self.parse_date("May 10 2026") == "2026-05-10"
        assert self.parse_date("January 15 2026") == "2026-01-15"

    def test_slash_format(self):
        assert self.parse_date("15/05/2026") == "2026-05-15"

    def test_invalid_date_returns_none(self):
        assert self.parse_date("not a date at all") is None

    def test_calculate_days_inclusive(self):
        assert self.calculate_days("2026-05-10", "2026-05-12") == 3

    def test_calculate_days_single_day(self):
        assert self.calculate_days("2026-05-10", "2026-05-10") == 1

    def test_calculate_days_invalid(self):
        """End before start should return -1 or negative."""
        result = self.calculate_days("2026-05-15", "2026-05-10")
        assert result <= 0


class TestLeaveBalance:
    """Integration tests — requires MySQL."""

    def test_balance_returns_all_types(self, employee_employee):
        from src.main_agent.agents.leave.executor import check_balance
        balance = check_balance(employee_employee["id"])
        assert "EL" in balance
        assert "CL" in balance
        assert "SL" in balance

    def test_balance_structure(self, employee_employee):
        from src.main_agent.agents.leave.executor import check_balance
        balance = check_balance(employee_employee["id"])
        for leave_type in ["EL", "CL", "SL"]:
            assert "used" in balance[leave_type]
            assert "allowed" in balance[leave_type]
            assert "remaining" in balance[leave_type]
            assert balance[leave_type]["remaining"] == (
                balance[leave_type]["allowed"] - balance[leave_type]["used"]
            )

    def test_balance_non_negative_remaining(self, employee_employee):
        from src.main_agent.agents.leave.executor import check_balance
        balance = check_balance(employee_employee["id"])
        for lt in ["EL", "CL", "SL"]:
            assert balance[lt]["remaining"] >= 0

    def test_balance_allowed_matches_policy(self, employee_employee):
        from src.main_agent.agents.leave.executor import check_balance, LEAVE_POLICY
        balance = check_balance(employee_employee["id"])
        for lt, policy_days in LEAVE_POLICY.items():
            assert balance[lt]["allowed"] == policy_days


class TestLeaveAgentWorkflow:
    """Unit tests for leave agent state machine — mocks DB calls."""

    def test_initial_step_asks_for_name(self, base_state):
        """When employee_id is 0 and step is initial, agent asks for name."""
        from src.main_agent.agents.leave.executor import leave_agent
        state = dict(base_state)
        state["employee_id"] = 0
        state["employee_name"] = ""
        state["input"] = ""
        result = leave_agent(state)
        assert result["step"] == "identify_employee"
        assert result["output"]

    def test_leave_type_el_detected(self, base_state):
        from src.main_agent.agents.leave.executor import leave_agent
        state = dict(base_state)
        state["step"] = "ask_leave_type"
        state["input"] = "earned leave"
        result = leave_agent(state)
        assert result["leave_data"].get("leave_type") == "EL"
        assert result["step"] == "ask_dates"

    def test_leave_type_cl_detected(self, base_state):
        from src.main_agent.agents.leave.executor import leave_agent
        state = dict(base_state)
        state["step"] = "ask_leave_type"
        state["input"] = "casual"
        result = leave_agent(state)
        assert result["leave_data"].get("leave_type") == "CL"

    def test_leave_type_sl_detected(self, base_state):
        from src.main_agent.agents.leave.executor import leave_agent
        state = dict(base_state)
        state["step"] = "ask_leave_type"
        state["input"] = "sick leave"
        result = leave_agent(state)
        assert result["leave_data"].get("leave_type") == "SL"

    def test_invalid_leave_type_asks_again(self, base_state):
        from src.main_agent.agents.leave.executor import leave_agent
        state = dict(base_state)
        state["step"] = "ask_leave_type"
        state["input"] = "vacation"
        result = leave_agent(state)
        assert result["step"] == "ask_leave_type"

    def test_date_parsing_in_workflow(self, base_state):
        from src.main_agent.agents.leave.executor import leave_agent
        state = dict(base_state)
        state["step"] = "ask_dates"
        state["leave_data"] = {"leave_type": "CL"}
        state["input"] = "2026-05-10 to 2026-05-12"
        result = leave_agent(state)
        assert result["leave_data"].get("start_date") == "2026-05-10"
        assert result["leave_data"].get("end_date") == "2026-05-12"
        assert result["leave_data"].get("days") == 3
        assert result["step"] == "ask_reason"
