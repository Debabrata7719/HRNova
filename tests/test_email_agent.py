"""
Test 2 — Email Agent
Tests: recipient parsing (name, all, department, email address).
Note: Actual email sending is NOT tested (would spam real inboxes).
      The send functions are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestRecipientParsing:
    """Unit tests for parse_recipients() — requires DB for name lookups."""

    def test_all_employees_keyword(self):
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients("send email to all employees")
        assert error is None
        assert len(recipients) >= 1

    def test_everyone_keyword(self):
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients("send to everyone")
        assert error is None
        assert len(recipients) >= 1

    def test_direct_email_address(self):
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients("send to test@example.com")
        assert error is None
        assert "test@example.com" in recipients

    def test_employee_name_lookup(self):
        """Should find Sayandip Bar by partial name."""
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients("send email to Sayandip")
        assert error is None
        assert len(recipients) >= 1
        assert "sayandip05@gmail.com" in recipients

    def test_employee_name_case_insensitive(self):
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients("send email to sayandip")
        assert error is None
        assert len(recipients) >= 1

    def test_hr_department(self):
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients("send to all HR employees")
        # HR department has at least 1 employee (Debabrata Dey)
        assert error is None
        assert len(recipients) >= 1

    def test_nonexistent_name_returns_error(self):
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients("send email to XYZNobodyExists12345")
        assert len(recipients) == 0
        assert error is not None

    def test_multiple_email_addresses(self):
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients(
            "send to alice@example.com and bob@example.com"
        )
        assert error is None
        assert "alice@example.com" in recipients
        assert "bob@example.com" in recipients

    def test_no_duplicates(self):
        from src.main_agent.agents.email.executor import parse_recipients
        recipients, error = parse_recipients("send to all employees")
        assert len(recipients) == len(set(recipients))


class TestEmailAgentWorkflow:
    """Tests for the email agent state machine — mocks actual sending."""

    def test_initial_step_asks_for_recipient(self, base_state):
        from src.main_agent.agents.email.executor import email_agent
        state = dict(base_state)
        state["input"] = ""
        result = email_agent(state)
        assert result["step"] == "ask_recipient"
        assert result["output"]

    def test_valid_recipient_advances_to_ask_body(self, base_state):
        from src.main_agent.agents.email.executor import email_agent
        state = dict(base_state)
        state["input"] = "send email to sayandip"
        result = email_agent(state)
        assert result["step"] == "ask_body"
        assert "sayandip05@gmail.com" in str(result["output"])

    def test_invalid_recipient_stays_on_ask_recipient(self, base_state):
        from src.main_agent.agents.email.executor import email_agent
        state = dict(base_state)
        state["input"] = "XYZNobodyExists99999"
        result = email_agent(state)
        assert result["step"] == "ask_recipient"

    @patch("src.main_agent.agents.email.executor.send_bulk_email")
    def test_body_step_triggers_send(self, mock_send, base_state):
        """When body is provided, send_bulk_email should be called."""
        mock_send.return_value = (True, "✅ Email sent successfully to 1 recipient(s)!")
        from src.main_agent.agents.email.executor import email_agent
        state = dict(base_state)
        state["step"] = "ask_body"
        state["email_data"] = {"recipients": ["test@example.com"]}
        state["input"] = "Hello, tomorrow is a holiday"
        result = email_agent(state)
        mock_send.assert_called_once()
        assert result["step"] == "completed"
        assert "sent" in result["output"].lower()

    @patch("src.main_agent.agents.email.executor.send_bulk_email")
    def test_send_failure_reported(self, mock_send, base_state):
        mock_send.return_value = (False, "❌ Failed to send email")
        from src.main_agent.agents.email.executor import email_agent
        state = dict(base_state)
        state["step"] = "ask_body"
        state["email_data"] = {"recipients": ["test@example.com"]}
        state["input"] = "Test message"
        result = email_agent(state)
        assert result["step"] == "completed"
        assert "failed" in result["output"].lower() or "❌" in result["output"]
