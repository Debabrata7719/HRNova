"""
Main router agent using LangGraph and StateGraph
Routes user input to different agents based on intent
Supports: email requests, leave requests, general chat
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from email_chatbot import email_agent
from leave_agent import leave_agent


# Define the state structure
class State(TypedDict):
    input: str
    intent: str
    step: str  # For step-based agents like leave_agent
    leave_data: dict  # For leave agent workflow
    output: str


def router(state: State) -> State:
    """
    Main router agent
    Takes user input and sets state["intent"] and delegates to appropriate agent

    Args:
        state: Dictionary with 'input' key

    Returns:
        state: Updated dictionary with agent response
    """
    user_input = state.get("input", "").lower()
    current_intent = state.get("intent", "")
    current_step = state.get("step", "initial")

    # If already in leave workflow (and not in initial/confirmation), continue with leave_agent
    if current_intent == "leave_request" and current_step not in [
        "initial",
        "confirm_leave",
        "completed",
    ]:
        return leave_agent(state)

    # If in leave confirmation step
    if current_step == "confirm_leave":
        if "yes" in user_input or "confirm" in user_input or user_input == "y":
            state["intent"] = "leave_request"
            state["step"] = "ask_name"
            state["leave_data"] = {}
            state["input"] = (
                ""  # Clear input so leave_agent asks for name without processing "yes"
            )
            return leave_agent(state)
        elif "no" in user_input or user_input == "n":
            state["intent"] = "general"
            state["step"] = "initial"
            state["output"] = (
                "Okay, cancelled. What else can I help you with?\n1. Email requests (type 'email')\n2. Leave requests (type 'leave')"
            )
            return state
        else:
            state["output"] = (
                "Please type 'yes' to proceed with leave request, or 'no' to cancel:"
            )
            return state

    # Check for leave request at the start
    if "leave" in user_input:
        state["intent"] = "leave_intent"
        state["step"] = "confirm_leave"
        state["output"] = "Do you want to apply for leave? (yes/no)"
        return state

    # Check for email request
    elif "email" in user_input:
        state["intent"] = "email_request"
        return email_agent(state)

    # Default to general info
    else:
        state["intent"] = "general"
        state["step"] = "initial"
        state["output"] = (
            "I can help you with:\n1. Email requests (type 'email')\n2. Leave requests (type 'leave')\n\nWhat would you like to do?"
        )
        return state


def build_graph():
    """
    Build LangGraph with StateGraph
    Routes to leave_agent, email_agent, or provides general help

    Returns:
        Compiled LangGraph
    """
    # Create StateGraph
    builder = StateGraph(State)

    # Add single router node that delegates to agents
    builder.add_node("router", router)

    # Set router as entry and exit point
    builder.set_entry_point("router")
    builder.add_edge("router", END)

    # Compile and return the graph
    return builder.compile()


def main():
    """
    Simple CLI loop for user interaction
    Takes user input, passes to graph, prints output
    Supports conversation state for step-based agents like leave_agent
    """
    # Build the graph
    graph = build_graph()

    print("NovaHR Assistant - Type your message (type 'exit' to quit)")
    print("-" * 60)
    print("Commands: 'email' for email requests, 'leave' for leave requests")
    print("-" * 60)

    # State for maintaining conversation context
    conversation_state: State = {
        "input": "",
        "intent": "",
        "step": "initial",
        "leave_data": {},
        "output": "",
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
