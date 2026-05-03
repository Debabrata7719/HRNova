"""
Employee Agent - Main interface for employees
Connects leave_agent (for leave applications) and query_agent (for policy/balance queries)
Run standalone: python employee_agent.py
"""

import argparse
from db_connection import get_db
from query_agent import query_agent
from leave_agent import leave_agent_standalone, find_employee, check_balance
from memory_manager import (
    create_memory_list_from_dict,
    serialize_memory_for_state,
    add_user_message_to_memory,
    add_assistant_message_to_memory,
)


def run_employee_agent():
    """Main employee agent loop"""
    print("\n=== NovaHR Employee Portal (type 'exit' to quit) ===\n")

    # Login
    print("Please login with your name")
    name = input("Enter your name: ").strip()
    if not name:
        print("Name is required.")
        return

    # Find employee
    emp = find_employee(name)
    if not emp:
        print(f"Employee '{name}' not found. Please contact HR.")
        return

    employee_id = emp["id"]
    employee_name = emp["name"]

    print(f"\nWelcome, {employee_name}!")
    print("I can help you with:")
    print("  1. Apply for leave")
    print("  2. Ask questions (policy, leave balance, etc.)")
    print("  3. Exit\n")

    # Initialize states
    leave_state = {
        "input": "",
        "step": "initial",
        "employee_id": employee_id,
        "employee_name": employee_name,
        "leave_data": {},
        "output": "",
    }

    query_state = {
        "input": "",
        "employee_id": employee_id,
        "query_agent_memory": {},
        "output": "",
    }

    current_agent = None  # "leave" or "query"

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            continue

        # Check if starting fresh
        if current_agent is None:
            user_lower = user_input.lower()

            # Check if wants leave
            if "1" in user_input or "leave" in user_lower or "apply" in user_lower:
                current_agent = "leave"
                leave_state["step"] = "initial"
                user_input = "apply leave"  # Start leave flow
                print("\n[Leave Application Mode]")

            # Check if wants query
            elif (
                "2" in user_input
                or "ask" in user_lower
                or "question" in user_lower
                or "policy" in user_lower
                or "balance" in user_lower
            ):
                current_agent = "query"
                print("\n[Query Mode]")

            else:
                print("I can help you:")
                print("  1. Apply for leave")
                print("  2. Ask questions (policy, leave balance, etc.)")
                continue

        # Process with appropriate agent
        if current_agent == "leave":
            leave_state["input"] = user_input
            leave_state = leave_agent_standalone(leave_state)
            print(f"\nBot: {leave_state['output']}")

            # Check if leave request completed
            if leave_state.get("step") == "completed":
                current_agent = None
                print("\nI can help you with:")
                print("  1. Apply for leave")
                print("  2. Ask questions (policy, leave balance, etc.)")

        elif current_agent == "query":
            # Skip processing if it's just the mode selection
            if user_input not in ["2", "ask", "question"]:
                query_state["input"] = user_input
                query_state = query_agent(query_state)
                print(f"\nBot: {query_state['output']}")

                # Check if query answered
                if query_state.get("step") == "completed":
                    current_agent = None
                    print("\nI can help you with:")
                    print("  1. Apply for leave")
                    print("  2. Ask questions (policy, leave balance, etc.)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Employee Agent")
    parser.add_argument(
        "--standalone", action="store_true", help="Run as standalone CLI"
    )
    args = parser.parse_args()

    if args.standalone or True:  # Default to standalone
        run_employee_agent()
    else:
        print("Use --standalone flag: python employee_agent.py --standalone")
