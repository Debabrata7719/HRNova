"""
Email agent for handling email-related requests
Extracts recipient, subject, and body from user input and sends emails
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
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


def email_agent(state):
    """
    Handle email-related requests with multi-step workflow
    Steps: initial → ask_recipient → ask_body → send_email → completed

    Args:
        state: Dictionary containing 'input', 'step', 'email_data' keys

    Returns:
        state: Updated dictionary with 'output' and 'step' keys
    """
    user_input = state.get("input", "").lower()
    step = state.get("step", "initial")
    email_data = state.get("email_data", {})

    # Extract email address using regex
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, state.get("input", ""))

    # ==================== STEP 1: ASK FOR RECIPIENT ====================
    if step == "initial" or step == "ask_recipient":
        if not user_input:
            state["output"] = (
                "I can help you send an email. Please provide:\n"
                "1. Recipient email address\n"
                "2. Message content\n\n"
                "Example: 'send email to john@example.com write Hello there'"
            )
            state["step"] = "ask_recipient"
        elif emails:
            recipient = emails[0]
            email_data["recipient"] = recipient
            state["email_data"] = email_data
            state["output"] = (
                f"Got it! I'll send to {recipient}. What should I write in the email body?"
            )
            state["step"] = "ask_body"
        else:
            state["output"] = (
                "I couldn't find a valid email address. Please provide a recipient email (e.g., john@example.com)"
            )
            state["step"] = "ask_recipient"

    # ==================== STEP 2: ASK FOR MESSAGE BODY ====================
    elif step == "ask_body":
        if not user_input or len(user_input) < 3:
            state["output"] = (
                "Please provide the message content (at least 3 characters)"
            )
            state["step"] = "ask_body"
        else:
            # Use the entire user input as the message body
            email_data["body"] = user_input
            state["email_data"] = email_data
            state["output"] = "Thank you. Let me send the email..."
            state["step"] = "send_email"

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
            state["output"] = (
                "Error: Missing recipient or message body. Please start over."
            )
            state["step"] = "initial"
            state["email_data"] = {}

    # ==================== DEFAULT ====================
    else:
        state["output"] = (
            "I can help you send an email. Please provide:\n"
            "1. Recipient email address\n"
            "2. Message content"
        )
        state["step"] = "ask_recipient"

    return state
