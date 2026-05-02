"""
Leave Management Agent for NovaHR
Step-based workflow for processing leave requests
"""

from datetime import datetime, timedelta
from db_connection import get_db

# Leave policy - days allowed per year
LEAVE_POLICY = {
    "EL": 18,  # Earned Leave
    "CL": 12,  # Casual Leave
    "SL": 12,  # Sick Leave
}


def parse_date(date_input: str) -> str:
    """
    Parse flexible date input and return YYYY-MM-DD format
    Handles formats like "2025-05-15", "15/05/2025", "May 15", "tomorrow", etc.

    Args:
        date_input (str): User input date

    Returns:
        str: Formatted date as YYYY-MM-DD, or None if invalid
    """
    date_input = date_input.strip().lower()

    # Handle special cases
    if date_input == "today":
        return datetime.now().strftime("%Y-%m-%d")
    elif date_input == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Try various date formats
    formats = [
        "%Y-%m-%d",  # 2025-05-15
        "%d/%m/%Y",  # 15/05/2025
        "%d-%m-%Y",  # 15-05-2025
        "%B %d, %Y",  # May 15, 2025
        "%d %B %Y",  # 15 May 2025
        "%d %b %Y",  # 15 May 2025 (short)
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_input, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def calculate_days(start_date: str, end_date: str) -> int:
    """
    Calculate number of days between two dates (inclusive)

    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format

    Returns:
        int: Number of days (or -1 if invalid)
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Validate dates
        if start > end:
            return -1

        # Calculate difference (inclusive of both days)
        days = (end - start).days + 1
        return days
    except ValueError:
        return -1


def get_employee(name: str):
    """
    Fetch employee from database by name

    Args:
        name (str): Employee name

    Returns:
        dict: Employee record or None if not found
    """
    db = get_db()
    query = "SELECT * FROM employees WHERE LOWER(name) = LOWER(%s)"
    result = db.execute_query(query, (name,))

    if result and len(result) > 0:
        return result[0]
    return None


def get_used_leaves(employee_id: int, leave_type: str) -> int:
    """
    Get total approved leave days used by employee for specific leave type

    Args:
        employee_id (int): Employee ID
        leave_type (str): Type of leave (EL/CL/SL)

    Returns:
        int: Total approved leave days used
    """
    db = get_db()
    query = """
    SELECT COALESCE(SUM(days), 0) as total_used
    FROM leaves
    WHERE employee_id = %s 
    AND leave_type = %s 
    AND status = 'approved'
    """
    result = db.execute_query(query, (employee_id, leave_type))

    if result and len(result) > 0:
        return result[0]["total_used"]
    return 0


def apply_leave(
    employee_id: int,
    leave_type: str,
    start_date: str,
    end_date: str,
    days: int,
    reason: str,
) -> dict:
    """
    Apply leave and check eligibility

    Args:
        employee_id (int): Employee ID
        leave_type (str): Type of leave (EL/CL/SL)
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        days (int): Number of days
        reason (str): Reason for leave

    Returns:
        dict: {status: 'approved'/'rejected', message: str, remaining: int}
    """
    db = get_db()

    # Check if leave type is valid
    if leave_type not in LEAVE_POLICY:
        return {
            "status": "rejected",
            "message": f"Invalid leave type. Allowed: {', '.join(LEAVE_POLICY.keys())}",
            "remaining": 0,
        }

    # Get allowed days for this leave type
    allowed_days = LEAVE_POLICY[leave_type]

    # Get already used days
    used_days = get_used_leaves(employee_id, leave_type)

    # Calculate remaining days
    remaining_days = allowed_days - used_days

    # Check if sufficient leaves available
    if (used_days + days) > allowed_days:
        return {
            "status": "rejected",
            "message": f"Insufficient {leave_type} balance. Requested: {days}, Available: {remaining_days}",
            "remaining": remaining_days,
        }

    # Get next leave_id
    max_id_query = "SELECT MAX(leave_id) as max_id FROM leaves"
    max_id_result = db.execute_query(max_id_query)

    if max_id_result and len(max_id_result) > 0:
        max_id = max_id_result[0].get("max_id") or 0
        new_leave_id = max_id + 1
    else:
        new_leave_id = 1

    # Insert leave record
    query = """
    INSERT INTO leaves (leave_id, employee_id, start_date, end_date, leave_type, days, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    last_id = db.insert_query(
        query,
        (new_leave_id, employee_id, start_date, end_date, leave_type, days, "approved"),
    )

    if last_id is not None and last_id > 0:
        new_remaining = remaining_days - days
        return {
            "status": "approved",
            "message": f"[OK] Leave approved! Leave ID: {new_leave_id}",
            "remaining": new_remaining,
        }
    else:
        # Check if insert actually succeeded even if lastrowid was 0
        check_query = "SELECT leave_id FROM leaves WHERE leave_id = %s"
        check_result = db.execute_query(check_query, (new_leave_id,))

        if check_result and len(check_result) > 0:
            new_remaining = remaining_days - days
            return {
                "status": "approved",
                "message": f"[OK] Leave approved! Leave ID: {new_leave_id}",
                "remaining": new_remaining,
            }
        else:
            return {
                "status": "rejected",
                "message": "Error inserting leave record. Please try again.",
                "remaining": remaining_days,
            }


def leave_agent(state):
    """
    Main leave agent with step-based workflow

    State structure:
    {
        "input": str,           # User input
        "step": str,            # Current step in workflow
        "leave_data": dict,     # Accumulated leave data
        "output": str           # Response message
    }

    Steps: ask_name → ask_type → ask_start_date → ask_end_date → ask_reason → confirm

    Args:
        state (dict): Current state

    Returns:
        dict: Updated state
    """

    current_step = state.get("step", "ask_name")
    leave_data = state.get("leave_data", {})
    user_input = state.get("input", "").strip()

    # Step 1: Ask for employee name
    if current_step == "ask_name":
        if not user_input:
            state["output"] = "Enter your name:"
            state["step"] = "ask_name"
        else:
            employee = get_employee(user_input)

            if employee:
                leave_data["employee_id"] = employee["id"]
                leave_data["employee_name"] = employee["name"]
                state["output"] = (
                    f"Welcome {employee['name']}!\n\nSelect leave type:\n1. EL (Earned Leave - 18 days)\n2. CL (Casual Leave - 12 days)\n3. SL (Sick Leave - 12 days)\n\nEnter EL, CL, or SL:"
                )
                state["step"] = "ask_type"
            else:
                state["output"] = (
                    f"Employee '{user_input}' not found. Please enter a valid name:"
                )
                state["step"] = "ask_name"

            state["leave_data"] = leave_data

    # Step 2: Ask for leave type
    elif current_step == "ask_type":
        if user_input.upper() in LEAVE_POLICY:
            leave_data["leave_type"] = user_input.upper()
            state["output"] = (
                f"Selected: {leave_data['leave_type']}\n\nEnter start date (format: YYYY-MM-DD, or 'today', 'tomorrow'):"
            )
            state["step"] = "ask_start_date"
            state["leave_data"] = leave_data
        else:
            state["output"] = "Invalid leave type. Please enter EL, CL, or SL:"
            state["step"] = "ask_type"

    # Step 3: Ask for start date
    elif current_step == "ask_start_date":
        parsed_date = parse_date(user_input)

        if parsed_date:
            leave_data["start_date"] = parsed_date
            state["output"] = (
                f"Start date set to: {parsed_date}\n\nEnter end date (format: YYYY-MM-DD, or 'today', 'tomorrow'):"
            )
            state["step"] = "ask_end_date"
            state["leave_data"] = leave_data
        else:
            state["output"] = (
                "Invalid date format. Please enter a valid date (YYYY-MM-DD, or 'today', 'tomorrow'):"
            )
            state["step"] = "ask_start_date"

    # Step 4: Ask for end date
    elif current_step == "ask_end_date":
        parsed_date = parse_date(user_input)

        if parsed_date:
            # Validate date range
            days = calculate_days(leave_data["start_date"], parsed_date)

            if days > 0:
                leave_data["end_date"] = parsed_date
                leave_data["days"] = days
                state["output"] = (
                    f"End date set to: {parsed_date}\nTotal days: {days}\n\nEnter reason for leave:"
                )
                state["step"] = "ask_reason"
                state["leave_data"] = leave_data
            else:
                state["output"] = (
                    "End date must be after start date. Please enter a valid end date:"
                )
                state["step"] = "ask_end_date"
        else:
            state["output"] = "Invalid date format. Please enter a valid date:"
            state["step"] = "ask_end_date"

    # Step 5: Ask for reason
    elif current_step == "ask_reason":
        if user_input and len(user_input) >= 5:
            leave_data["reason"] = user_input

            # Show summary
            summary = f"""
Leave Request Summary:
- Name: {leave_data["employee_name"]}
- Leave Type: {leave_data["leave_type"]}
- Start Date: {leave_data["start_date"]}
- End Date: {leave_data["end_date"]}
- Days: {leave_data["days"]}
- Reason: {leave_data["reason"]}

Type 'confirm' to submit, or 'cancel' to abort:
"""
            state["output"] = summary
            state["step"] = "confirm"
            state["leave_data"] = leave_data
        else:
            state["output"] = (
                "Reason must be at least 5 characters. Please enter a valid reason:"
            )
            state["step"] = "ask_reason"

    # Step 6: Confirm and process
    elif current_step == "confirm":
        if user_input.lower() == "confirm":
            # Process leave application
            result = apply_leave(
                leave_data["employee_id"],
                leave_data["leave_type"],
                leave_data["start_date"],
                leave_data["end_date"],
                leave_data["days"],
                leave_data["reason"],
            )

            if result["status"] == "approved":
                state["output"] = (
                    f"{result['message']}\nRemaining {leave_data['leave_type']} balance: {result['remaining']} days"
                )
            else:
                state["output"] = (
                    f"[REJECTED] Leave Rejected\n{result['message']}\nRemaining {leave_data['leave_type']} balance: {result['remaining']} days"
                )

            # Reset for next leave request
            state["step"] = "completed"
            state["leave_data"] = {}

        elif user_input.lower() == "cancel":
            state["output"] = "Leave request cancelled."
            state["step"] = "completed"
            state["leave_data"] = {}

        else:
            state["output"] = (
                "Invalid input. Type 'confirm' to submit or 'cancel' to abort:"
            )
            state["step"] = "confirm"

    # Completed state
    elif current_step == "completed":
        state["output"] = (
            "Leave request process completed. Type 'leave' to submit another request."
        )
        state["step"] = "completed"

    return state
