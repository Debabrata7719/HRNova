"""
Email agent for handling email-related requests
Extracts recipient, subject, and body from user input and sends emails
Now includes conversation history with ConversationBufferWindowMemory (window: 5)
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from src.main_agent.memory import (
    create_memory_list_from_dict,
    serialize_memory_for_state,
    add_user_message_to_memory,
    add_assistant_message_to_memory,
)
from langsmith import traceable
import re

# Load environment variables
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(recipient: str, subject: str, body: str) -> tuple[bool, str]:
    """
    Send an email using Gmail SMTP

    Args:
        recipient: Email address of recipient
        subject: Subject line
        body: Email body content

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = recipient
        message["Subject"] = subject

        # Add body
        message.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(message)

        return True, f"Email sent successfully to {recipient}!"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


@traceable(name="Email Agent")
def email_agent(state):
    """
    Handle email-related requests with multi-step workflow and conversation memory.
    Steps: initial → ask_recipient → ask_body → send_email → completed

    Uses ConversationBufferWindowMemory with a window size of 5 messages.
    When the window fills, old messages are automatically summarized before being dropped.

    Args:
        state: Dictionary containing 'input', 'step', 'email_data', 'email_agent_memory' keys

    Returns:
        state: Updated dictionary with 'output', 'step', 'email_data', and 'email_agent_memory' keys
    """
    user_input = state.get("input", "").lower()
    step = state.get("step", "initial")
    email_data = state.get("email_data", {})

    # Extract memory from state (window size: 5)
    memory_dict = state.get("email_agent_memory", {})
    memory = create_memory_list_from_dict(memory_dict)
    # Ensure correct window size for email_agent
    memory.window_size = 5

    # Add user input to memory
    add_user_message_to_memory(memory, state.get("input", ""))

    # Extract email address using regex
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, state.get("input", ""))

    # ==================== STEP 1: ASK FOR RECIPIENT ====================
    if step == "initial" or step == "ask_recipient":
        if not user_input:
            response = (
                "I can help you send an email. Please provide:\n"
                "1. Recipient email address\n"
                "2. Message content\n\n"
                "Example: 'send email to john@example.com write Hello there'"
            )
            state["output"] = response
            state["step"] = "ask_recipient"
        elif emails:
            recipient = emails[0]
            email_data["recipient"] = recipient
            state["email_data"] = email_data
            response = f"Got it! I'll send to {recipient}. What should I write in the email body?"
            state["output"] = response
            state["step"] = "ask_body"
        else:
            response = "I couldn't find a valid email address. Please provide a recipient email (e.g., john@example.com)"
            state["output"] = response
            state["step"] = "ask_recipient"

    # ==================== STEP 2: ASK FOR MESSAGE BODY ====================
    elif step == "ask_body":
        if not user_input or len(user_input) < 1:
            response = "Please provide the message content"
            state["output"] = response
            state["step"] = "ask_body"
        else:
            # Use the entire user input as the message body
            email_data["body"] = user_input
            state["email_data"] = email_data

            # Immediately proceed to send the email
            recipient = email_data.get("recipient", "")
            body = email_data.get("body", "")

            if recipient and body:
                subject = "Message"
                # Actually send the email
                success, message = send_email(recipient, subject, body)
                state["output"] = message
                state["step"] = "completed"
            else:
                response = "Error: Missing recipient. Please start over."
                state["output"] = response
                state["step"] = "initial"
                state["email_data"] = {}

    # ==================== STEP 3: SEND EMAIL ====================
    elif step == "send_email":
        recipient = email_data.get("recipient", "")
        body = email_data.get("body", "")

        if recipient and body:
            subject = "Message"
            # Actually send the email
            success, message = send_email(recipient, subject, body)
            state["output"] = message
            state["step"] = "completed"
        else:
            response = "Error: Missing recipient or message body. Please start over."
            state["output"] = response
            state["step"] = "initial"
            state["email_data"] = {}

    # ==================== DEFAULT ====================
    else:
        response = (
            "I can help you send an email. Please provide:\n"
            "1. Recipient email address\n"
            "2. Message content"
        )
        state["output"] = response
        state["step"] = "ask_recipient"

    # Add assistant response to memory
    add_assistant_message_to_memory(memory, state["output"])

    # Serialize memory back to state
    state["email_agent_memory"] = serialize_memory_for_state(memory)

    return state
