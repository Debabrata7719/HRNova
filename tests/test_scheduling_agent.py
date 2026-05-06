"""
Test 5 — Scheduling Agent
Tests: datetime parsing (IST-aware), LLM response parsing.
Note: Actual Google Calendar API calls are NOT tested (requires OAuth).
"""
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class TestDatetimeParsing:
    """Unit tests for parse_to_datetime() — no external deps."""

    def setup_method(self):
        from src.main_agent.agents.scheduling.executor import parse_to_datetime
        self.parse = parse_to_datetime

    def test_tomorrow_3pm_ist_aware(self):
        dt = self.parse("tomorrow", "15:00")
        assert dt.tzinfo is not None, "datetime must be timezone-aware"
        assert dt.hour == 15
        assert dt.minute == 0

    def test_today_10am(self):
        dt = self.parse("today", "10:00")
        assert dt.hour == 10
        assert dt.tzinfo is not None

    def test_iso_string_offset(self):
        """isoformat() must include +05:30 for IST."""
        dt = self.parse("tomorrow", "15:00")
        iso = dt.isoformat()
        assert "+05:30" in iso, f"Expected +05:30 in ISO string, got: {iso}"

    def test_specific_date(self):
        dt = self.parse("2026-05-20", "14:00")
        assert dt.year == 2026
        assert dt.month == 5
        assert dt.day == 20
        assert dt.hour == 14

    def test_default_time_when_missing(self):
        """Empty time string should default to 09:00."""
        dt = self.parse("tomorrow", "")
        assert dt.hour == 9

    def test_timezone_is_ist(self):
        dt = self.parse("tomorrow", "15:00")
        # UTC offset for IST is +5:30 = 19800 seconds
        offset = dt.utcoffset()
        assert offset.total_seconds() == 19800


class TestScheduleAgentWorkflow:
    """Tests for schedule agent state machine — mocks Google Calendar."""

    def test_initial_step_parses_input(self, base_state):
        """Agent should parse date/time from initial input."""
        from unittest.mock import patch, MagicMock
        mock_data = {
            "title": "Meeting",
            "date": "tomorrow",
            "time": "15:00",
            "description": "client meeting"
        }
        with patch(
            "src.main_agent.agents.scheduling.executor.parse_datetime_with_llm",
            return_value=mock_data
        ):
            from src.main_agent.agents.scheduling.executor import schedule_agent
            state = dict(base_state)
            state["input"] = "schedule a meeting tomorrow at 3pm for client"
            result = schedule_agent(state)
            assert result["step"] == "confirm"
            assert "15:00" in result["output"] or "3:00" in result["output"]

    def test_confirm_yes_calls_calendar(self, base_state):
        """Confirming with 'yes' should call create_calendar_event."""
        from unittest.mock import patch
        with patch(
            "src.main_agent.agents.scheduling.executor.create_calendar_event",
            return_value={"success": True, "message": "Event created: https://calendar.google.com/event?eid=test"}
        ):
            from src.main_agent.agents.scheduling.executor import schedule_agent
            state = dict(base_state)
            state["step"] = "confirm"
            state["title"] = "Meeting"
            state["date"] = "tomorrow"
            state["time"] = "15:00"
            state["description"] = ""
            state["input"] = "yes"
            result = schedule_agent(state)
            assert result["step"] == "completed"
            assert "scheduled" in result["output"].lower() or "meeting" in result["output"].lower()

    def test_confirm_no_cancels(self, base_state):
        from src.main_agent.agents.scheduling.executor import schedule_agent
        state = dict(base_state)
        state["step"] = "confirm"
        state["title"] = "Meeting"
        state["date"] = "tomorrow"
        state["time"] = "15:00"
        state["description"] = ""
        state["input"] = "no"
        result = schedule_agent(state)
        assert result["step"] == "initial"
        assert "cancel" in result["output"].lower()

    def test_calendar_error_reported(self, base_state):
        from unittest.mock import patch
        with patch(
            "src.main_agent.agents.scheduling.executor.create_calendar_event",
            return_value={"success": False, "message": "No credentials"}
        ):
            from src.main_agent.agents.scheduling.executor import schedule_agent
            state = dict(base_state)
            state["step"] = "confirm"
            state["title"] = "Meeting"
            state["date"] = "tomorrow"
            state["time"] = "15:00"
            state["description"] = ""
            state["input"] = "yes"
            result = schedule_agent(state)
            assert result["step"] == "completed"
            assert "error" in result["output"].lower() or "no credentials" in result["output"].lower()
