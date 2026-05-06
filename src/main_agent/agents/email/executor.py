"""
Email agent for handling email-related requests
Extracts recipient, subject, and body from user input and sends emails
Now includes conversation history with ConversationBufferWindowMemory (window: 5)

Features:
- Send emails by employee name (looks up from database)
- Send to multiple recipients
- Send to "all employees"
- Integrate with employee database
"""

import re
import yagmail
from src.config import get_settings
from src.logger import get_logger
from src.main_agent.memory import (
    create_memory_list_from_dict,
    serialize_memory_for_state,
    add_user_message_to_memory,
    add_assistant_message_to_memory,
)
from src.tools.db_connection import get_db
from langsmith import traceable

logger = get_logger(__name__)
_settings = get_settings()


def find_employee_by_name(name: str) -> dict:
    """
    Find employee by name in database
    
    Args:
        name: Employee name (partial match supported)
    
    Returns:
        dict: Employee data with id, name, email or None if not found
    """
    db = get_db()
    query = """
    SELECT id, name, email 
    FROM employees 
    WHERE LOWER(name) LIKE %s
    LIMIT 1
    """
    result = db.execute_query(query, (f"%{name.lower()}%",))
    return result[0] if result else None


def get_all_employees() -> list:
    """
    Get all employees from database
    
    Returns:
        list: List of employee dicts with id, name, email
    """
    db = get_db()
    query = "SELECT id, name, email FROM employees"
    result = db.execute_query(query)
    return result if result else []


def get_employees_by_department(department: str) -> list:
    """
    Get all employees from a specific department
    
    Args:
        department: Department name (partial match supported)
    
    Returns:
        list: List of employee dicts with id, name, email, department
    """
    db = get_db()
    query = """
    SELECT id, name, email, department 
    FROM employees 
    WHERE LOWER(department) LIKE %s
    """
    result = db.execute_query(query, (f"%{department.lower()}%",))
    return result if result else []


def parse_recipients(user_input: str) -> tuple[list, str]:
    """
    Parse recipients from user input
    Supports:
    - Email addresses: john@example.com
    - Employee names: "send to Sayandip" or "send to debabrata"
    - Multiple recipients: "send to Sayandip and Debabrata"
    - All employees: "send to all employees" or "send to everyone"
    - Department: "send to all HR employees" or "send to HR department"
    
    Args:
        user_input: User's message
    
    Returns:
        tuple: (list of email addresses, error message if any)
    """
    recipients = []
    user_lower = user_input.lower()
    
    # Check for department-based sending
    # Patterns: "all HR employees", "HR department", "all engineering team"
    department_patterns = [
        r"all\s+(\w+)\s+(?:employees|department|team|staff)",
        r"(\w+)\s+department",
        r"everyone\s+in\s+(\w+)",
    ]
    
    for pattern in department_patterns:
        matches = re.findall(pattern, user_lower)
        if matches:
            department = matches[0]
            # Skip generic words
            if department not in ["the", "all", "every", "employee", "employees"]:
                employees = get_employees_by_department(department)
                if employees:
                    recipients = [emp["email"] for emp in employees if emp.get("email")]
                    return recipients, None
                else:
                    return [], f"No employees found in '{department}' department"
    
    # Check for "all employees" or "everyone" (with variations)
    all_keywords = [
        "all employees", "all employee", "everyone", "everybody",
        "all staff", "entire team", "whole team", "all team"
    ]
    if any(phrase in user_lower for phrase in all_keywords):
        employees = get_all_employees()
        if employees:
            recipients = [emp["email"] for emp in employees if emp.get("email")]
            return recipients, None
        else:
            return [], "No employees found in database"
    
    # Extract email addresses using regex
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, user_input)
    recipients.extend(emails)
    
    # Extract names - look for words after "to", "send", "email"
    # First try capitalized names
    name_patterns = [
        r"(?:send\s+(?:email\s+)?(?:to\s+)?|email\s+(?:to\s+)?|to\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:and\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:,\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    ]
    
    names = []
    for pattern in name_patterns:
        matches = re.findall(pattern, user_input)
        names.extend(matches)
    
    # If no capitalized names found, try lowercase names
    if not names:
        # Extract words after "to", "send", "email" even if lowercase
        lowercase_patterns = [
            r"(?:send\s+(?:email\s+)?(?:to\s+)?|email\s+(?:to\s+)?|to\s+)([a-z]+(?:\s+[a-z]+)?)",
        ]
        for pattern in lowercase_patterns:
            matches = re.findall(pattern, user_lower)
            # Capitalize first letter for database lookup
            for match in matches:
                if len(match) > 2:  # Skip very short words
                    # Capitalize each word
                    capitalized = ' '.join(word.capitalize() for word in match.split())
                    names.append(capitalized)
    
    # Look up each name in database
    for name in names:
        name = name.strip()
        if name and len(name) > 1:  # Avoid single letters
            # Skip common words that aren't names
            skip_words = [
                "email", "send", "message", "write", "all", "everyone", 
                "employee", "employees", "department", "team", "staff",
                "the", "and", "or", "to", "from", "for"
            ]
            if name.lower() in skip_words:
                continue
                
            employee = find_employee_by_name(name)
            if employee and employee.get("email"):
                recipients.append(employee["email"])
    
    # Remove duplicates
    recipients = list(set(recipients))
    
    if not recipients:
        return [], "No valid recipients found. Please provide employee names or email addresses."
    
    return recipients, None


def send_email(recipient: str, subject: str, body: str) -> tuple[bool, str]:
    """
    Send an email using yagmail (Gmail SMTP wrapper).

    Args:
        recipient: Email address of recipient
        subject: Subject line
        body: Email body content

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        yag = yagmail.SMTP(
            user=_settings.EMAIL_ADDRESS,
            password=_settings.EMAIL_APP_PASSWORD,
        )
        yag.send(to=recipient, subject=subject, contents=body)
        logger.info("Email sent to %s", recipient)
        return True, f"Email sent successfully to {recipient}!"
    except Exception as e:
        logger.error("Failed to send email to %s: %s", recipient, e)
        return False, f"Failed to send email: {str(e)}"


def send_bulk_email(recipients: list, subject: str, body: str) -> tuple[bool, str]:
    """
    Send email to multiple recipients using a single yagmail session.

    Args:
        recipients: List of email addresses
        subject: Subject line
        body: Email body content

    Returns:
        tuple: (success: bool, message: str)
    """
    if not recipients:
        return False, "No recipients provided"

    success_count = 0
    failed_count = 0

    try:
        yag = yagmail.SMTP(
            user=_settings.EMAIL_ADDRESS,
            password=_settings.EMAIL_APP_PASSWORD,
        )
        for recipient in recipients:
            try:
                yag.send(to=recipient, subject=subject, contents=body)
                success_count += 1
                logger.info("Email sent to %s", recipient)
            except Exception as e:
                failed_count += 1
                logger.error("Failed to send to %s: %s", recipient, e)
    except Exception as e:
        logger.error("SMTP session failed: %s", e)
        return False, f"❌ Could not connect to email server: {str(e)}"

    if failed_count == 0:
        return True, f"✅ Email sent successfully to {success_count} recipient(s)!"
    elif success_count == 0:
        return False, f"❌ Failed to send email to all {failed_count} recipient(s)"
    else:
        return True, f"⚠️ Email sent to {success_count} recipient(s), failed for {failed_count}"


@traceable(name="Email Agent")
def email_agent(state):
    """
    Handle email-related requests with multi-step workflow and conversation memory.
    Steps: initial → ask_recipient → ask_body → send_email → completed

    Features:
    - Send by employee name: "send email to Sayandip"
    - Send to multiple: "send to Sayandip and Debabrata"
    - Send to all: "send to all employees"
    - Send by email: "send to john@example.com"

    Uses ConversationBufferWindowMemory with a window size of 5 messages.

    Args:
        state: Dictionary containing 'input', 'step', 'email_data', 'email_agent_memory' keys

    Returns:
        state: Updated dictionary with 'output', 'step', 'email_data', and 'email_agent_memory' keys
    """
    user_input = state.get("input", "")
    step = state.get("step", "initial")
    email_data = state.get("email_data", {})

    # Extract memory from state (window size: 5)
    memory_dict = state.get("email_agent_memory", {})
    memory = create_memory_list_from_dict(memory_dict)
    memory.window_size = 5

    # Add user input to memory
    add_user_message_to_memory(memory, user_input)

    # ==================== STEP 1: ASK FOR RECIPIENT ====================
    if step == "initial" or step == "ask_recipient":
        if not user_input:
            response = (
                "I can help you send an email. You can:\n"
                "• Send to an employee: 'send email to Sayandip'\n"
                "• Send to multiple: 'send to Sayandip and Debabrata'\n"
                "• Send to all: 'send to all employees'\n"
                "• Send by email: 'send to john@example.com'\n\n"
                "Who would you like to send the email to?"
            )
            state["output"] = response
            state["step"] = "ask_recipient"
        else:
            # Parse recipients from input
            recipients, error = parse_recipients(user_input)
            
            if error:
                response = f"❌ {error}\n\nPlease provide employee names or email addresses."
                state["output"] = response
                state["step"] = "ask_recipient"
            else:
                email_data["recipients"] = recipients
                state["email_data"] = email_data
                
                # Show confirmation
                if len(recipients) == 1:
                    response = f"✅ Got it! I'll send to: {recipients[0]}\n\nWhat should I write in the email?"
                else:
                    recipient_list = "\n  • ".join(recipients)
                    response = f"✅ Got it! I'll send to {len(recipients)} recipient(s):\n  • {recipient_list}\n\nWhat should I write in the email?"
                
                state["output"] = response
                state["step"] = "ask_body"

    # ==================== STEP 2: ASK FOR MESSAGE BODY ====================
    elif step == "ask_body":
        if not user_input or len(user_input.strip()) < 1:
            response = "Please provide the message content"
            state["output"] = response
            state["step"] = "ask_body"
        else:
            # Use the entire user input as the message body
            email_data["body"] = user_input
            state["email_data"] = email_data

            # Immediately proceed to send the email
            recipients = email_data.get("recipients", [])
            body = email_data.get("body", "")

            if recipients and body:
                subject = "Message from NovaHR"
                
                # Send to all recipients
                success, message = send_bulk_email(recipients, subject, body)
                state["output"] = message
                state["step"] = "completed"
                
                # Clear email data for next request
                state["email_data"] = {}
            else:
                response = "❌ Error: Missing recipients. Please start over."
                state["output"] = response
                state["step"] = "initial"
                state["email_data"] = {}

    # ==================== DEFAULT ====================
    else:
        response = (
            "I can help you send an email. You can:\n"
            "• Send to an employee: 'send email to Sayandip'\n"
            "• Send to multiple: 'send to Sayandip and Debabrata'\n"
            "• Send to all: 'send to all employees'\n"
            "• Send by email: 'send to john@example.com'"
        )
        state["output"] = response
        state["step"] = "ask_recipient"

    # Add assistant response to memory
    add_assistant_message_to_memory(memory, state["output"])

    # Serialize memory back to state
    state["email_agent_memory"] = serialize_memory_for_state(memory)

    return state
