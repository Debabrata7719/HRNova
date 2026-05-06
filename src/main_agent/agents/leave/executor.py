"""
Leave Management Agent for NovaHR - Simplified Non-LLM Version
Step-based workflow for processing leave requests
"""

import argparse
from datetime import datetime, timedelta
import dateutil.parser
from src.tools.db_connection import get_db
from src.logger import get_logger
from src.main_agent.memory import (
    create_memory_list_from_dict,
    serialize_memory_for_state,
    add_user_message_to_memory,
    add_assistant_message_to_memory,
)
from langsmith import traceable

logger = get_logger(__name__)

# Leave policy - days allowed per year
LEAVE_POLICY = {
    "EL": 18,  # Earned Leave
    "CL": 12,  # Casual Leave
    "SL": 12,  # Sick Leave
}


def parse_date(date_input: str) -> str:
    """
    Parse flexible date input and return YYYY-MM-DD format.
    Handles ISO format directly to avoid dateutil day/month swap bug.
    """
    date_input = date_input.strip().lower()

    if date_input == "today":
        return datetime.now().strftime("%Y-%m-%d")
    if date_input in ("tomorrow", "next day"):
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Handle ISO format directly — dateutil with dayfirst=True swaps day/month
    # e.g. "2026-05-10" would become "2026-10-05" if passed to dateutil
    import re
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_input):
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            return date_input  # already correct format
        except ValueError:
            return None

    # For all other formats (May 10, 15/05/2026, etc.) use dateutil
    try:
        parsed = dateutil.parser.parse(date_input, dayfirst=True)
        return parsed.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        return None


def calculate_days(start_date: str, end_date: str) -> int:
    """Calculate number of days between two dates (inclusive)"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days + 1
    except:
        return -1


def check_balance(employee_id: int) -> dict:
    """
    Check leave balance for an employee for all leave types.

    Args:
        employee_id: The employee ID

    Returns:
        Dict with leave type as key and {used, allowed, remaining} as value
    """
    db = get_db()
    balance = {}

    for leave_type in LEAVE_POLICY:
        query = """
        SELECT COALESCE(SUM(days), 0) as total_used
        FROM leaves
        WHERE employee_id = %s 
        AND leave_type = %s 
        AND status IN ('approved', 'pending')
        """
        result = db.execute_query(query, (employee_id, leave_type))
        used_days = result[0]["total_used"] if result else 0
        allowed_days = LEAVE_POLICY[leave_type]
        balance[leave_type] = {
            "used": used_days,
            "allowed": allowed_days,
            "remaining": allowed_days - used_days,
        }

    return balance


def find_employee(name: str) -> dict:
    """Find employee by name"""
    db = get_db()
    query = "SELECT id, name, email, department FROM employees WHERE name = %s"
    result = db.execute_query(query, (name,))
    if result:
        return {"id": result[0]["id"], "name": result[0]["name"]}
    return None


@traceable(name="Leave Agent")
def leave_agent(state: dict) -> dict:
    """
    Simple rule-based leave request handler (no LLM required)
    Supports multi-turn conversations with memory stored in State

    Uses ConversationBufferWindowMemory with a window size of 10 messages.
    When the window fills, old messages are automatically summarized before being dropped.

    Args:
        state: Dictionary containing input, employee_id, employee_name, leave_data, and leave_agent_memory

    Returns:
        Updated state with output, step, leave_agent_memory, and other fields
    """
    user_input = state.get("input", "").strip().lower()
    employee_id = state.get("employee_id", 0)
    employee_name = state.get("employee_name", "")
    step = state.get("step", "initial")

    # Extract memory from state (window size: 10)
    memory_dict = state.get("leave_agent_memory", {})
    memory = create_memory_list_from_dict(memory_dict)
    # Ensure correct window size for leave_agent
    memory.window_size = 10

    # Add user input to memory
    add_user_message_to_memory(memory, state.get("input", ""))

    try:
        # ==================== STEP 1: IDENTIFY EMPLOYEE ====================
        if step == "initial" or step == "identify_employee":
            # Always ask for name when starting fresh
            if not user_input or step == "initial":
                response = (
                    "Hi! I'm here to help with your leave request. What's your name?"
                )
                state["step"] = "identify_employee"
            else:
                # Try to find employee in database (search by name)
                db = get_db()
                query = "SELECT id, name FROM employees WHERE LOWER(name) LIKE %s"
                result = db.execute_query(query, (f"%{user_input.lower()}%",))

                if result:
                    emp = result[0]
                    state["employee_id"] = emp["id"]
                    state["employee_name"] = emp["name"]
                    response = f"Great! I found you: {emp['name']}. What type of leave do you need? (EL, CL, or SL)"
                    state["step"] = "ask_leave_type"
                else:
                    response = f"I couldn't find an employee named '{user_input}'. Please provide your exact name."
                    state["step"] = "identify_employee"

        # ==================== STEP 2: GET LEAVE TYPE ====================
        elif step == "ask_leave_type":
            leave_type = None
            if "el" in user_input or "earned" in user_input:
                leave_type = "EL"
            elif "cl" in user_input or "casual" in user_input:
                leave_type = "CL"
            elif "sl" in user_input or "sick" in user_input:
                leave_type = "SL"

            if leave_type:
                leave_data = state.get("leave_data", {})
                leave_data["leave_type"] = leave_type
                state["leave_data"] = leave_data
                response = f"Got it, you need {leave_type}. When do you want to take leave? (e.g., '2026-05-05 to 2026-05-06')"
                state["step"] = "ask_dates"
            else:
                response = "Please specify leave type: EL (Earned Leave), CL (Casual Leave), or SL (Sick Leave)"
                state["step"] = "ask_leave_type"

        # ==================== STEP 3: GET DATES ====================
        elif step == "ask_dates":
            # Try to parse dates from input
            if " to " in user_input or "-" in user_input:
                if " to " in user_input:
                    parts = user_input.split(" to ")
                else:
                    parts = user_input.split("-")

                if len(parts) == 2:
                    start_date = parse_date(parts[0].strip())
                    end_date = parse_date(parts[1].strip())

                    if start_date and end_date:
                        days = calculate_days(start_date, end_date)
                        if days > 0:
                            leave_data = state.get("leave_data", {})
                            leave_data["start_date"] = start_date
                            leave_data["end_date"] = end_date
                            leave_data["days"] = days
                            state["leave_data"] = leave_data
                            response = f"I see, {days} days from {start_date} to {end_date}. Any reason for this leave?"
                            state["step"] = "ask_reason"
                        else:
                            response = "Invalid date range. Start date must be before end date. Please try again."
                            state["step"] = "ask_dates"
                    else:
                        response = "I couldn't parse those dates. Please use format: '2026-05-05' or 'May 5'"
                        state["step"] = "ask_dates"
                else:
                    response = "Please provide both start and end dates separated by 'to' (e.g., '2026-05-05 to 2026-05-06')"
                    state["step"] = "ask_dates"
            else:
                response = (
                    "Please provide date range (e.g., '2026-05-05 to 2026-05-06')"
                )
                state["step"] = "ask_dates"

        # ==================== STEP 4: GET REASON ====================
        elif step == "ask_reason":
            if user_input and len(user_input) > 3:
                leave_data = state.get("leave_data", {})
                leave_data["reason"] = user_input
                state["leave_data"] = leave_data
                response = "Thank you. Let me verify your request and submit it..."
                state["step"] = "confirm_request"
            else:
                response = "Please provide a reason for your leave request."
                state["step"] = "ask_reason"

        # ==================== STEP 5: CONFIRM AND SUBMIT ====================
        elif step == "confirm_request":
            # Use leave_data from state
            leave_data = state.get("leave_data", {})

            if all(
                k in leave_data
                for k in ["leave_type", "start_date", "end_date", "days", "reason"]
            ):
                # Check balance
                db = get_db()
                emp_id = state.get("employee_id")
                leave_type = leave_data["leave_type"]

                query = """
                SELECT COALESCE(SUM(days), 0) as total_used
                FROM leaves
                WHERE employee_id = %s 
                AND leave_type = %s 
                AND status IN ('approved', 'pending')
                """
                result = db.execute_query(query, (emp_id, leave_type))
                used_days = result[0]["total_used"] if result else 0
                allowed_days = LEAVE_POLICY[leave_type]
                remaining_days = allowed_days - used_days

                if used_days + leave_data["days"] <= allowed_days:
                    # Submit leave request
                    insert_query = """
                    INSERT INTO leaves 
                    (employee_id, start_date, end_date, leave_type, days, status, reason, submitted_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    db.insert_query(
                        insert_query,
                        (
                            emp_id,
                            leave_data["start_date"],
                            leave_data["end_date"],
                            leave_type,
                            leave_data["days"],
                            "pending",
                            leave_data["reason"],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )

                    response = f"Leave request submitted successfully! {leave_data['days']} days of {leave_type} approved for {leave_data['start_date']} to {leave_data['end_date']}. Remaining balance: {remaining_days - leave_data['days']} days"
                    state["step"] = "completed"
                else:
                    response = f"Insufficient {leave_type} balance. You have {remaining_days} days available, but requested {leave_data['days']} days."
                    state["step"] = "completed"
            else:
                response = (
                    "Could not submit request. Missing information. Starting over..."
                )
                state["step"] = "initial"

        else:
            response = "Hi! I'm here to help with your leave request. What's your name?"
            state["step"] = "identify_employee"

    except Exception as e:
        logger.error("Leave agent error: %s", e)
        response = f"Error processing request: {str(e)}"
        state["step"] = "error"

    # Add response to memory
    add_assistant_message_to_memory(memory, response)

    # Set output
    state["output"] = response

    # Serialize memory back to state
    state["leave_agent_memory"] = serialize_memory_for_state(memory)

    return state


def leave_agent_standalone(state: dict) -> dict:
    """
    Conversational leave workflow for standalone mode.
    Similar to leave_agent but simplified for CLI.
    """
    user_input = state.get("input", "").strip().lower()
    step = state.get("step", "initial")
    employee_id = state.get("employee_id", 0)
    leave_data = state.get("leave_data", {})

    # Step 1: Ask what they want to do
    if step == "initial":
        if "balance" in user_input or "2" in user_input:
            balance = check_balance(employee_id)
            response = "\n--- Your Leave Balance ---\n"
            for lt in ["EL", "CL", "SL"]:
                names = {"EL": "Earned", "CL": "Casual", "SL": "Sick"}
                response += f"{lt} ({names[lt]}): {balance[lt]['used']} used, {balance[lt]['remaining']} remaining out of {balance[lt]['allowed']}\n"
            state["output"] = response
            state["step"] = "completed"
        elif "leave" in user_input or "1" in user_input:
            state["output"] = "What type of leave do you need? (EL, CL, or SL)"
            state["step"] = "ask_leave_type"
        else:
            state["output"] = (
                "I can help you apply for leave or check your balance. What would you like?"
            )
            state["step"] = "initial"

    # Step 2: Get leave type
    elif step == "ask_leave_type":
        leave_type = None
        if "el" in user_input or "earned" in user_input:
            leave_type = "EL"
        elif "cl" in user_input or "casual" in user_input:
            leave_type = "CL"
        elif "sl" in user_input or "sick" in user_input:
            leave_type = "SL"

        if leave_type:
            leave_data["leave_type"] = leave_type
            state["leave_data"] = leave_data
            state["output"] = (
                f"Got it, {leave_type}. When do you want to take leave? (e.g., '2026-05-05 to 2026-05-06')"
            )
            state["step"] = "ask_dates"
        else:
            state["output"] = (
                "Please specify: EL (Earned Leave), CL (Casual Leave), or SL (Sick Leave)"
            )

    # Step 3: Get dates
    elif step == "ask_dates":
        # Handle "tomorrow to", "today to", "from tomorrow to", etc.
        user_input_clean = user_input.replace("from ", "").strip()

        if " to " in user_input_clean:
            parts = user_input_clean.split(" to ")
        elif "-" in user_input_clean:
            parts = user_input_clean.split("-")
        else:
            state["output"] = (
                "Please provide date range (e.g., 'tomorrow to 2026-05-06' or '2026-05-05 to 2026-05-06')"
            )
            return state

        if len(parts) == 2:
            start_input = parts[0].strip()
            end_input = parts[1].strip()

            # Parse start date (handle "tomorrow", "today")
            if start_input == "tomorrow":
                start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif start_input == "today":
                start_date = datetime.now().strftime("%Y-%m-%d")
            else:
                start_date = parse_date(start_input)

            # Parse end date
            if end_input == "tomorrow":
                end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif end_input == "today":
                end_date = datetime.now().strftime("%Y-%m-%d")
            else:
                end_date = parse_date(end_input)

            if start_date and end_date:
                days = calculate_days(start_date, end_date)
                if days > 0:
                    leave_data["start_date"] = start_date
                    leave_data["end_date"] = end_date
                    leave_data["days"] = days
                    state["leave_data"] = leave_data
                    state["output"] = (
                        f"I see, {days} days from {start_date} to {end_date}. Any reason for this leave?"
                    )
                    state["step"] = "submit_request"
                else:
                    state["output"] = (
                        "Invalid date range. Start date must be before end date."
                    )
            else:
                state["output"] = (
                    "I couldn't parse those dates. Please use format: 'tomorrow to 2026-05-06' or '2026-05-05 to 2026-05-06'"
                )
        else:
            state["output"] = (
                "Please provide both start and end dates separated by 'to' (e.g., 'tomorrow to 2026-05-06')"
            )

    # Step 4: Get reason and auto-submit
    elif step == "submit_request":
        if user_input and len(user_input) > 3:
            leave_data["reason"] = user_input
            state["leave_data"] = leave_data

            # Get leave details
            leave_type = leave_data.get("leave_type")
            start_date = leave_data.get("start_date")
            end_date = leave_data.get("end_date")
            days = leave_data.get("days")
            reason = user_input

            if all([leave_type, start_date, end_date, days]):
                # Check balance
                balance = check_balance(employee_id)
                remaining = balance[leave_type]["remaining"]

                if days <= remaining:
                    # Submit to DB
                    db = get_db()
                    insert_query = """
                    INSERT INTO leaves 
                    (employee_id, start_date, end_date, leave_type, days, status, reason, submitted_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    db.insert_query(
                        insert_query,
                        (
                            employee_id,
                            start_date,
                            end_date,
                            leave_type,
                            days,
                            "pending",
                            reason,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                    new_remaining = remaining - days
                    state["output"] = (
                        f"Leave request submitted successfully!\n\n"
                        f"Type: {leave_type}\n"
                        f"Dates: {start_date} to {end_date}\n"
                        f"Days: {days}\n"
                        f"Remaining {leave_type}: {new_remaining} days"
                    )
                    state["step"] = "completed"
                else:
                    state["output"] = (
                        f"Insufficient {leave_type} balance. You have {remaining} days available, but requested {days} days."
                    )
                    state["step"] = "completed"
            else:
                state["output"] = "Could not submit. Missing information."
                state["step"] = "completed"
        else:
            state["output"] = "Please provide a reason for your leave request."

    else:
        state["output"] = "I can help you apply for leave or check your balance."
        state["step"] = "initial"

    return state
