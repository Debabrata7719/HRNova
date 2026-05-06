"""
Test — Router Intent Detection
Tests all routing cases: correct agent selection, HR-only blocking, edge cases.
"""
import pytest


class TestRouterIntentDetection:
    """Unit tests for the LangGraph router — no LLM, no DB needed."""

    def _route(self, user_input, role="HR", base_state=None):
        from src.main_agent.router import router
        state = base_state or {
            "input": user_input, "step": "initial", "intent": "", "role": role,
            "leave_data": {}, "email_data": {}, "schedule_data": {},
            "output": "", "employee_id": 1, "employee_name": "Debabrata Dey",
            "schedule_title": "", "schedule_date": "", "schedule_time": "",
            "schedule_description": "", "leave_agent_memory": {},
            "email_agent_memory": {}, "general_agent_memory": {},
            "query_agent_memory": {}, "schedule_agent_memory": {},
            "long_term_memory": [], "session_summaries": {}
        }
        state["input"] = user_input
        state["role"] = role
        return router(state)

    # ── Schedule Agent ────────────────────────────────────────────────────────

    def test_schedule_meeting_hr(self):
        result = self._route("schedule a meeting tomorrow at 3pm", role="HR")
        assert result["intent"] == "schedule_request"

    def test_book_meeting_hr(self):
        result = self._route("book a meeting on Friday at 2pm", role="HR")
        assert result["intent"] == "schedule_request"

    def test_set_up_meeting_hr(self):
        result = self._route("set up a meeting with the team", role="HR")
        assert result["intent"] == "schedule_request"

    def test_schedule_blocked_for_employee(self):
        result = self._route("schedule a meeting tomorrow at 3pm", role="EMPLOYEE")
        assert result["intent"] == "general"
        assert result["step"] == "completed"  # router sets output directly

    def test_question_about_past_meeting_goes_to_general(self):
        """'did you schedule any meeting' is a question, not an action."""
        result = self._route("did you schedule any meeting earlier", role="HR")
        assert result["intent"] == "general"

    def test_meeting_word_alone_goes_to_general(self):
        """Just mentioning 'meeting' without action phrase → general."""
        result = self._route("what happened in the last meeting", role="HR")
        assert result["intent"] == "general"

    # ── Email Agent ───────────────────────────────────────────────────────────

    def test_send_email_action(self):
        result = self._route("send an email to all employees")
        assert result["intent"] == "email_request"

    def test_send_email_to_name(self):
        result = self._route("send email to Sayandip about the deadline")
        assert result["intent"] == "email_request"

    def test_write_email(self):
        result = self._route("write an email to the HR team")
        assert result["intent"] == "email_request"

    def test_send_word_alone_not_email(self):
        """'send me the policy' should NOT trigger email agent."""
        result = self._route("send me the leave policy document")
        assert result["intent"] != "email_request"

    # ── Leave Agent ───────────────────────────────────────────────────────────

    def test_apply_for_leave(self):
        result = self._route("I want to apply for casual leave")
        assert result["intent"] == "leave_request"

    def test_request_leave(self):
        result = self._route("I need to request leave for next week")
        assert result["intent"] == "leave_request"

    def test_take_leave(self):
        result = self._route("I want to take leave tomorrow")
        assert result["intent"] == "leave_request"

    def test_apply_for_sick_leave(self):
        result = self._route("apply for sick leave")
        assert result["intent"] == "leave_request"

    # ── Query Agent ───────────────────────────────────────────────────────────

    def test_leave_balance_query(self):
        result = self._route("what is my leave balance")
        assert result["intent"] == "query_request"

    def test_leave_status_query(self):
        result = self._route("show my leave requests")
        assert result["intent"] == "query_request"

    def test_is_leave_approved(self):
        result = self._route("is my leave approved")
        assert result["intent"] == "query_request"

    def test_casual_leave_policy(self):
        result = self._route("what is the casual leave policy")
        assert result["intent"] == "query_request"

    def test_sick_leave_policy(self):
        result = self._route("explain sick leave policy")
        assert result["intent"] == "query_request"

    # ── General Agent ─────────────────────────────────────────────────────────

    def test_hello_goes_to_general(self):
        result = self._route("hello")
        assert result["intent"] == "general"

    def test_who_are_you_goes_to_general(self):
        result = self._route("who are you")
        assert result["intent"] == "general"

    def test_what_can_you_do_goes_to_general(self):
        result = self._route("what can you do")
        assert result["intent"] == "general"

    def test_random_question_goes_to_general(self):
        result = self._route("how is the weather today")
        assert result["intent"] == "general"

    # ── Workflow preservation ─────────────────────────────────────────────────

    def test_intent_preserved_mid_workflow(self):
        """If step is not initial/completed, intent should not change."""
        from src.main_agent.router import router
        state = {
            "input": "personal work",  # reason for leave — contains no action phrase
            "step": "ask_reason",
            "intent": "leave_request",  # already in leave workflow
            "role": "HR",
            "leave_data": {"leave_type": "CL"},
            "email_data": {}, "schedule_data": {},
            "output": "", "employee_id": 1, "employee_name": "Debabrata Dey",
            "schedule_title": "", "schedule_date": "", "schedule_time": "",
            "schedule_description": "", "leave_agent_memory": {},
            "email_agent_memory": {}, "general_agent_memory": {},
            "query_agent_memory": {}, "schedule_agent_memory": {},
            "long_term_memory": [], "session_summaries": {}
        }
        result = router(state)
        assert result["intent"] == "leave_request"  # must not change

    def test_step_resets_after_completed(self):
        """After step=completed, next message should reset step to initial."""
        from src.main_agent.router import router
        state = {
            "input": "hello",
            "step": "completed",
            "intent": "leave_request",
            "role": "HR",
            "leave_data": {}, "email_data": {}, "schedule_data": {},
            "output": "Leave submitted!", "employee_id": 1, "employee_name": "Debabrata Dey",
            "schedule_title": "", "schedule_date": "", "schedule_time": "",
            "schedule_description": "", "leave_agent_memory": {},
            "email_agent_memory": {}, "general_agent_memory": {},
            "query_agent_memory": {}, "schedule_agent_memory": {},
            "long_term_memory": [], "session_summaries": {}
        }
        result = router(state)
        assert result["step"] == "initial"
