"""
Main router agent using LangGraph and StateGraph
Routes user input to different agents based on intent
Supports: email requests, leave requests

Now includes:
- Proper LangGraph routing
- LangSmith tracing
- Clean state handling
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from email_chatbot import email_agent
from leave_agent import leave_agent
from general_agent import general_agent
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
    output: str
    employee_id: int
    employee_name: str


# ==================== ROUTER ====================
@traceable(name="Router")
def router(state: State) -> State:
    """
    Detects intent ONLY (no agent calls)
    Preserves existing intent if we're in the middle of a workflow
    """
    user_input = state.get("input", "").lower()
    current_step = state.get("step", "initial")

    # Only detect new intent if starting fresh
    if current_step == "initial":
        if "leave" in user_input:
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
) -> Literal["leave_agent", "email_agent", "general_agent"]:
    """
    Controls routing between agents
    """

    current_intent = state.get("intent", "")
    current_step = state.get("step", "initial")

    # 🔥 Continue leave workflow if active
    if current_intent == "leave_request" and current_step not in [
        "initial",
        "completed",
    ]:
        return "leave_agent"

    # 🔥 Fresh routing
    if current_intent == "leave_request":
        return "leave_agent"
    elif current_intent == "email_request":
        return "email_agent"
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
            "general_agent": "general_agent",
        },
    )

    # Leave Agent Loop
    builder.add_conditional_edges(
        "leave_agent",
        lambda state: "leave_agent" if state.get("step") != "completed" else "end",
        {
            "leave_agent": "leave_agent",
            "end": END,
        },
    )

    # Email Agent → End (completes in one shot per step)
    builder.add_edge("email_agent", END)

    # General Agent → End
    builder.add_edge("general_agent", END)

    return builder.compile()


# ==================== MAIN LOOP ====================
def main():
    graph = build_graph()

    # Create graph folder
    # os.makedirs("graphs", exist_ok=True)

    # # Show graph structure
    # print(graph.get_graph().draw_mermaid())

    print("\n🚀 NovaHR Assistant Started (type 'exit' to quit)\n")

    # Initial state
    conversation_state: State = {
        "input": "",
        "intent": "",
        "step": "initial",
        "leave_data": {},
        "email_data": {},
        "output": "",
        "employee_id": 0,
        "employee_name": "",
    }

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            # Update input
            conversation_state["input"] = user_input

            # Only reset intent when starting fresh (step is "initial")
            if conversation_state.get("step") == "initial":
                conversation_state["intent"] = ""

            # Run graph
            result = graph.invoke(conversation_state)

            # Update state
            conversation_state = result

            # Output
            print(f"\nBot: {result['output']}")

        except Exception as e:
            print(f"Error: {e}")


# ==================== RUN ====================
if __name__ == "__main__":
    main()
