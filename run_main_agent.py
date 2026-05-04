import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main_agent import run_main_agent, State
from dotenv import load_dotenv

load_dotenv()

BANNER = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    ███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ██╗  ██╗██████╗  ║
║    ████╗  ██║██╔═══██╗██║   ██║██╔══██╗██║  ██║██╔══██╗ ║
║    ██╔██╗ ██║██║   ██║██║   ██║███████║███████║██████╔╝ ║
║    ██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║██╔══██║██╔══██╗ ║
║    ██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║██║  ██║██║  ██║ ║
║    ╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ║
║                                                          ║
║           AI-Powered HR Assistant Platform               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Available Commands:

📧 Email     → "send email to all employees about holiday"
🏖️  Leave    → "apply for casual leave from tomorrow to Friday"
📅 Schedule  → "schedule a meeting tomorrow at 3pm"
🔍 Query     → "what is the leave policy" / "check my leave balance"
💬 General   → just chat naturally

Type 'help'  → show this menu
Type 'exit'  → quit NovaHR
"""


def get_initial_state() -> dict:
    """Returns a fresh initial state"""
    return {
        "input": "",
        "intent": "",
        "step": "initial",
        "leave_data": {},
        "email_data": {},
        "schedule_data": {},
        "output": "",
        "employee_id": 0,
        "employee_name": "",
        "schedule_title": "",
        "schedule_date": "",
        "schedule_time": "",
        "schedule_description": "",
        "leave_agent_memory": {},
        "email_agent_memory": {},
        "general_agent_memory": {},
        "query_agent_memory": {},
        "schedule_agent_memory": {},
        "session_summaries": {},
    }


def should_reset_state(state: dict) -> bool:
    """
    Returns True if the conversation is done and state should be reset for a fresh start.
    
    Only resets when step is completed AND intent is email (one-shot) or general (stateless).
    Leave, schedule, query are multi-turn so preserve state.
    """
    step = state.get("step", "initial")
    intent = state.get("intent", "")
    
    if step == "completed" and intent in ["email_request", "general"]:
        return True
    
    return False


def main():
    print(BANNER)
    print("  Welcome to NovaHR — Your AI-Powered HR Assistant")
    print("  Type 'help' to see available commands\n")
    
    state = get_initial_state()
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! Have a great day 👋")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() == "exit":
            print("\nGoodbye! Have a great day 👋")
            break
        
        if user_input.lower() == "help":
            print(HELP_TEXT)
            continue
        
        # Inject user input into state
        state["input"] = user_input
        
        try:
            # Run through LangGraph pipeline
            state = run_main_agent(state)
            
            # Print response
            output = state.get("output", "")
            if output:
                print(f"\nNovaHR: {output}\n")
            else:
                print("\nNovaHR: I didn't get a response. Please try again.\n")
            
            # Reset state if conversation is complete
            if should_reset_state(state):
                # Preserve memories across resets so agents remember context
                preserved_memories = {
                    "leave_agent_memory":    state.get("leave_agent_memory", {}),
                    "email_agent_memory":    state.get("email_agent_memory", {}),
                    "general_agent_memory":  state.get("general_agent_memory", {}),
                    "query_agent_memory":    state.get("query_agent_memory", {}),
                    "schedule_agent_memory": state.get("schedule_agent_memory", {}),
                    "session_summaries":     state.get("session_summaries", {}),
                }
                state = get_initial_state()
                state.update(preserved_memories)
        
        except Exception as e:
            print(f"\nNovaHR: Something went wrong — {str(e)}\n")
            print("Resetting state...\n")
            state = get_initial_state()


if __name__ == "__main__":
    main()
