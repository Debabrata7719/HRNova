"""
Main router agent using LangGraph and StateGraph
Routes user input to different agents based on intent
Supports: email requests, leave requests, employee queries, scheduling

Now includes:
- Proper LangGraph routing
- LangSmith tracing
- Clean state handling
- Query agent for employee balance/policy questions
- Schedule agent for Google Calendar integration
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from src.main_agent.agents.email.executor import email_agent
from src.main_agent.agents.leave.executor import leave_agent
from src.main_agent.agents.general.executor import general_agent
from src.main_agent.agents.query.executor import query_agent as employee_query_agent
from src.main_agent.agents.scheduling.executor import schedule_agent
from dotenv import load_dotenv
from langsmith import traceable
import os

# Load environment variables (.env)
load_dotenv()


# ==================== STATE STRUCTURE ====================
class State(TypedDict):
    input: str
    intent: str
    step: str
    leave_data: dict
    email_data: dict
    schedule_data: dict
    output: str
    employee_id: int
    employee_name: str
    role: str  # "HR" or "EMPLOYEE" — controls access to schedule agent

    # Schedule agent fields
    schedule_title: str
    schedule_date: str
    schedule_time: str
    schedule_description: str

    # ConversationBufferWindowMemory for each sub-agent
    leave_agent_memory: dict  # Serialized ConversationBufferWindowMemory
    email_agent_memory: dict  # Serialized ConversationBufferWindowMemory
    general_agent_memory: dict  # Serialized ConversationBufferWindowMemory
    query_agent_memory: dict  # Serialized ConversationBufferWindowMemory
    schedule_agent_memory: dict  # Serialized ConversationBufferWindowMemory

    # Long-term memory (ChromaDB)
    long_term_memory: list  # Retrieved memories from ChromaDB
    
    # For future long-term memory coordination
    session_summaries: dict  # Summaries of each agent's actions


# ==================== ROUTER ====================
@traceable(name="Router")
def router(state: State) -> State:
    """
    Detects intent ONLY (no agent calls).
    Uses action-phrase matching — a keyword alone is NOT enough,
    the user must express clear intent to perform that action.

    Priority:
    1. Schedule Agent — explicit create/book/set up a meeting (HR only)
    2. Email Agent    — explicit send/compose/write an email
    3. Leave Agent    — explicit apply/request/take leave
    4. Query Agent    — questions about leave balance, status, policy
    5. General Agent  — everything else (conversation, questions about past events, etc.)
    """
    user_input = state.get("input", "").lower().strip()
    current_step = state.get("step", "initial")
    role = state.get("role", "EMPLOYEE").upper()

    if current_step in ["initial", "completed"]:
        if current_step == "completed":
            state["step"] = "initial"

        # ── PRIORITY 1: Schedule Agent ────────────────────────────────
        # Must be an ACTION phrase — not just a question containing "meeting"
        schedule_action_phrases = [
            "schedule a meeting", "schedule meeting",
            "book a meeting", "book meeting",
            "set up a meeting", "set up meeting",
            "create a meeting", "create meeting",
            "add to calendar", "add a calendar",
            "create an event", "add an event",
            "plan a meeting", "arrange a meeting",
            # follow-up phrases like "do same for tomorrow 4pm"
            "do same for", "same meeting for", "same for tomorrow",
            "same for today", "repeat meeting", "reschedule",
            "another meeting", "one more meeting",
        ]
        is_schedule_action = any(p in user_input for p in schedule_action_phrases)

        if is_schedule_action:
            if role == "HR":
                state["intent"] = "schedule_request"
            else:
                state["intent"] = "general"
                state["output"] = (
                    "Sorry, scheduling meetings is only available to HR. "
                    "I can help you with leave requests or policy questions."
                )
                state["step"] = "completed"

        # ── PRIORITY 2: Email Agent ───────────────────────────────────
        # Must be an ACTION phrase — not just a question mentioning "email"
        elif any(p in user_input for p in [
            "send an email", "send email", "send a mail",
            "write an email", "write email",
            "compose an email", "compose email",
            "email to ", "mail to ",
        ]):
            state["intent"] = "email_request"

        # ── PRIORITY 3: Leave Agent ───────────────────────────────────
        # Explicit apply/request/take leave actions
        elif any(p in user_input for p in [
            "apply for leave", "apply leave",
            "request leave", "request for leave",
            "take leave", "take a leave",
            "want to take leave", "want leave",
            "need leave", "need to take leave",
            "book leave", "book a leave",
            "i want to apply", "i need to apply",
            "can i apply", "apply for",
            "submit leave", "raise leave",
        ]):
            state["intent"] = "leave_request"

        # ── PRIORITY 4: Query Agent ───────────────────────────────────
        # Questions about leave data or HR policy
        elif any(p in user_input for p in [
            "leave balance", "my balance",
            "how many leave", "leaves remaining", "leaves left",
            "leave status", "my leave status",
            "is my leave", "is me apply",
            "leave approved", "leave pending", "leave rejected",
            "leave policy", "casual leave policy",
            "sick leave policy", "earned leave policy",
            "what is casual leave", "what is sick leave",
            "what is earned leave", "explain leave",
            "check my leave", "show my leave",
            "my leave request", "leave history",
        ]):
            state["intent"] = "query_request"

        # ── PRIORITY 5: General fallback ──────────────────────────────
        else:
            state["intent"] = "general"

    return state


# ==================== ROUTE DECISION ====================
@traceable(name="Route Decision")
def route_decision(
    state: State,
) -> Literal[
    "leave_agent", "email_agent", "query_agent", "schedule_agent", "general_agent"
]:
    """
    Controls routing between agents
    """

    current_intent = state.get("intent", "")
    current_step = state.get("step", "initial")

    # If router already handled the request (e.g. blocked schedule for employee),
    # route to general_agent which will just pass through the existing output
    if current_step == "completed" and state.get("output"):
        return "general_agent"

    # Continue leave workflow if active
    if current_intent == "leave_request" and current_step not in [
        "initial",
        "completed",
    ]:
        return "leave_agent"

    # Continue query workflow if active
    if current_intent == "query_request" and current_step not in [
        "initial",
        "completed",
    ]:
        return "query_agent"

    # Continue schedule workflow if active
    if current_intent == "schedule_request" and current_step not in [
        "initial",
        "completed",
    ]:
        return "schedule_agent"

    # Fresh routing
    if current_intent == "leave_request":
        return "leave_agent"
    elif current_intent == "email_request":
        return "email_agent"
    elif current_intent == "query_request":
        return "query_agent"
    elif current_intent == "schedule_request":
        return "schedule_agent"
    elif current_intent == "general":
        return "general_agent"

    # fallback to general for unknown intents
    return "general_agent"


# ==================== BUILD GRAPH ====================
def build_graph():
    builder = StateGraph(State)

    # Nodes
    builder.add_node("router", router)
    builder.add_node("leave_agent", leave_agent)
    builder.add_node("email_agent", email_agent)
    builder.add_node("query_agent", employee_query_agent)
    builder.add_node("schedule_agent", schedule_agent)
    builder.add_node("general_agent", general_agent)

    # Entry
    builder.set_entry_point("router")

    # Router → Agents
    builder.add_conditional_edges(
        "router",
        route_decision,
        {
            "leave_agent": "leave_agent",
            "email_agent": "email_agent",
            "query_agent": "query_agent",
            "schedule_agent": "schedule_agent",
            "general_agent": "general_agent",
        },
    )

    # Leave Agent → End
    builder.add_edge("leave_agent", END)

    # Email Agent → End
    builder.add_edge("email_agent", END)

    # Query Agent → End
    builder.add_edge("query_agent", END)

    # Schedule Agent → End
    builder.add_edge("schedule_agent", END)

    # General Agent → End
    builder.add_edge("general_agent", END)

    return builder.compile()
