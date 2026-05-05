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
    Detects intent ONLY (no agent calls)
    Preserves existing intent if we're in the middle of a workflow
    Resets intent when user starts a new request (step is initial or completed)
    """
    user_input = state.get("input", "").lower()
    current_step = state.get("step", "initial")
    role = state.get("role", "EMPLOYEE").upper()

    # Detect new intent when starting fresh or starting new request
    if current_step in ["initial", "completed"]:
        # Reset step when starting new request
        if current_step == "completed":
            state["step"] = "initial"
        # Schedule is HR-only — redirect employees to general with a message
        if (
            "schedule" in user_input
            or "meeting" in user_input
            or "calendar" in user_input
        ):
            if role == "HR":
                state["intent"] = "schedule_request"
            else:
                state["intent"] = "general"
                state["output"] = "Sorry, scheduling meetings is only available to HR. I can help you with leave requests or policy questions."
                state["step"] = "completed"
        # Check for query intents
        elif "balance" in user_input or "policy" in user_input:
            state["intent"] = "query_request"
        elif "leave" in user_input:
            state["intent"] = "leave_request"
        elif "email" in user_input:
            state["intent"] = "email_request"
        else:
            state["intent"] = "general"
    # If we're already in a workflow, preserve the current intent
    # (don't override based on keywords that might appear in body text)

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
