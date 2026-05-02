"""
Leave Management Agent for NovaHR - Simplified Non-LLM Version
Step-based workflow for processing leave requests
No LLM dependency to avoid rate limit issues
"""

from datetime import datetime, timedelta
from db_connection import get_db

# Leave policy - days allowed per year
LEAVE_POLICY = {
    "EL": 18,  # Earned Leave
    "CL": 12,  # Casual Leave
    "SL": 12,  # Sick Leave
}

# Conversation memory store for multi-turn support
conversation_memory_store = {}


class ConversationMemory:
    """Manages in-memory conversation history"""

    def __init__(self, employee_id: int, employee_name: str, max_messages: int = 100):
        self.employee_id = employee_id
        self.employee_name = employee_name
        self.messages: list[dict] = []
        self.max_messages = max_messages
        self.created_at = datetime.now()
        self.leave_request = {}  # Store leave details

    def add_message(self, role: str, content: str):
        """Add message to memory"""
        self.messages.append({"role": role, "content": content})

        # Keep only recent messages if exceeds max
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def set_leave_data(self, **kwargs):
        """Store leave request details"""
        self.leave_request.update(kwargs)

    def get_leave_data(self):
        """Get leave request details"""
        return self.leave_request

    def clear(self):
        """Clear memory"""
        self.messages = []
        self.leave_request = {}


def parse_date(date_input: str) -> str:
    """Parse flexible date input and return YYYY-MM-DD format"""
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
    """Calculate number of days between two dates (inclusive)"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days + 1
    except:
        return -1


def leave_agent(state: dict) -> dict:
    """
    Simple rule-based leave request handler (no LLM required)
    Supports multi-turn conversations with memory
    """
    user_input = state.get("input", "").strip().lower()
    employee_id = state.get("employee_id", 0)
    employee_name = state.get("employee_name", "")
    step = state.get("step", "initial")

    # Get or create memory for this employee
    if employee_id == 0:
        temp_key = "temp_user"
        if temp_key not in conversation_memory_store:
            conversation_memory_store[temp_key] = ConversationMemory(0, "User")
        memory = conversation_memory_store[temp_key]
    else:
        if employee_id not in conversation_memory_store:
            conversation_memory_store[employee_id] = ConversationMemory(
                employee_id, employee_name
            )
        memory = conversation_memory_store[employee_id]

    # Add user input to memory
    memory.add_message("user", user_input)

    try:
        # ==================== STEP 1: IDENTIFY EMPLOYEE ====================
        if step == "initial" or step == "identify_employee":
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
                    memory.employee_id = emp["id"]
                    memory.employee_name = emp["name"]
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
                memory.set_leave_data(leave_type=leave_type)
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
                            memory.set_leave_data(
                                start_date=start_date, end_date=end_date, days=days
                            )
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
                memory.set_leave_data(reason=user_input)
                response = "Thank you. Let me verify your request and submit it..."
                state["step"] = "confirm_request"
            else:
                response = "Please provide a reason for your leave request."
                state["step"] = "ask_reason"

        # ==================== STEP 5: CONFIRM AND SUBMIT ====================
        elif step == "confirm_request":
            # Use leave_data from state (persisted by previous steps)
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
                AND status IN ('approved', 'pending_approval')
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
                            "pending_approval",
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
        response = f"Error processing request: {str(e)}"
        state["step"] = "error"

    # Add response to memory
    memory.add_message("assistant", response)

    # Set output
    state["output"] = response

    # Ensure employee info is in state
    if memory.employee_id > 0:
        state["employee_id"] = memory.employee_id
        state["employee_name"] = memory.employee_name

    # Persist leave_data from memory to state for state management
    state["leave_data"] = memory.get_leave_data()

    return state
