"""
Main router agent using LangGraph and StateGraph
Routes user input to different agents based on intent
Supports: email requests, leave requests, general chat

Uses proper LangGraph routing with:
- router node: Intent detection only
- route_decision: Conditional routing logic
- leave_agent node: Multi-step workflow with internal looping
- email_agent node: Single-step workflow
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from email_chatbot import email_agent
from leave_agent import leave_agent, conversation_memory_store


# Define the state structure
class State(TypedDict):
    input: str
    intent: str
    step: str  # For step-based agents like leave_agent
    leave_data: dict  # For leave agent workflow
    output: str
    employee_id: int  # For leave agent
    employee_name: str  # For leave agent


def router(state: State) -> State:
    """
    Intent detection node - ONLY detects intent, does NOT call agents

    Sets state["intent"] based on user input keywords.
    PRESERVES existing intent if we're in an active workflow (step != initial/completed).
    The routing decision is made by route_decision(), not by this node.

    Args:
        state: Current state with 'input' key

    Returns:
        state: Updated with detected intent
    """
    user_input = state.get("input", "").lower()
    current_step = state.get("step", "initial")
    current_intent = state.get("intent", "")

    # CRITICAL: If in an active workflow, preserve the intent
    # This allows leave_agent to continue processing multi-step requests
    if current_step not in ["initial", "completed"]:
        # Already in a workflow, don't reset intent
        return state

    # Check for leave request keyword
    if "leave" in user_input:
        state["intent"] = "leave_request"
        state["output"] = ""  # Output will be set by leave_agent
    # Check for email request keyword
    elif "email" in user_input:
        state["intent"] = "email_request"
        state["output"] = ""  # Output will be set by email_agent
    # Default to general
    else:
        state["intent"] = "general"
        state["output"] = (
            "I can help you with:\n1. Email requests (type 'email')\n2. Leave requests (type 'leave')\n\nWhat would you like to do?"
        )

    return state


def route_decision(state: State) -> Literal["leave_agent", "email_agent", "router"]:
    """
    Conditional edge function - Routes based on intent AND workflow state

    CRITICAL LOGIC:
    - If leave workflow is active (step != initial/completed),
      ALWAYS route to leave_agent to continue the multi-step flow
    - Otherwise, route based on intent
    - Default back to router for unknown intents

    Args:
        state: Current state with 'intent' and 'step' keys

    Returns:
        str: Next node name ("leave_agent", "email_agent", or "router")
    """
    current_intent = state.get("intent", "")
    current_step = state.get("step", "initial")

    # CRITICAL: If leave workflow is active, continue with leave_agent
    # This ensures multi-step workflows don't get interrupted
    if current_intent == "leave_request" and current_step not in [
        "initial",
        "completed",
    ]:
        return "leave_agent"

    # Route based on intent for fresh requests
    if current_intent == "leave_request":
        return "leave_agent"
    elif current_intent == "email_request":
        return "email_agent"
    else:
        # Unknown intent, back to router for more input
        return "router"


def build_graph():
    """
    Build LangGraph with proper routing architecture

    Graph structure:
    - router: Intent detection node
    - route_decision: Conditional edge to route based on intent
    - leave_agent: Multi-step node with internal looping
    - email_agent: Single-step node

    leave_agent loops internally until step == "completed"
    email_agent goes directly to END

    Returns:
        Compiled LangGraph
    """
    # Create StateGraph
    builder = StateGraph(State)

    # ==================== ADD NODES ====================

    # Router node - intent detection only
    builder.add_node("router", router)

    # Leave agent node - multi-step workflow
    builder.add_node("leave_agent", leave_agent)

    # Email agent node - single-step workflow
    builder.add_node("email_agent", email_agent)

    # ==================== SET ENTRY POINT ====================
    builder.set_entry_point("router")

    # ==================== ROUTING FROM ROUTER ====================
    builder.add_conditional_edges(
        "router",
        route_decision,
        {
            "email_agent": "email_agent",
            "leave_agent": "leave_agent",
            "router": END,  # Changed: unknown intents go to END
        },
    )

    # ==================== LEAVE AGENT EXIT ====================
    # Leave agent always goes to END (single invocation per user input)
    builder.add_edge("leave_agent", END)

    # ==================== EMAIL AGENT EXIT ====================
    # Email agent always goes to END (single-step workflow)
    builder.add_edge("email_agent", END)

    # ==================== COMPILE AND RETURN ====================
    return builder.compile()


import os


def main():
    """
    Simple CLI loop for user interaction
    Takes user input, passes to graph, prints output
    Supports conversation state for step-based agents like leave_agent
    """
    # Build the graph
    graph = build_graph()
    os.makedirs("graphs", exist_ok=True)

    # 🔥 Save graph inside graphs folder
    print(graph.get_graph().draw_mermaid())
    print("NovaHR Assistant - How can i help you ?!  or type 'exit' to quit)")

    # State for maintaining conversation context
    conversation_state: State = {
        "input": "",
        "intent": "",
        "step": "initial",
        "leave_data": {},
        "output": "",
        "employee_id": 0,
        "employee_name": "",
    }

    while True:
        # Take user input
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            # Update input in state
            conversation_state["input"] = user_input

            # ONLY reset intent if we're truly starting fresh (not in a confirmation or active workflow)
            if conversation_state.get("step") in [
                "completed",
                "initial",
            ] and conversation_state.get("intent") in ["", "general"]:
                conversation_state["intent"] = ""

            # Pass to graph
            result = graph.invoke(conversation_state)

            # Update conversation state with result for next iteration
            conversation_state = result

            # Print output
            print(f"\nBot: {result['output']}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
