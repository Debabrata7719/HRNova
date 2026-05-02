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
    Handle email-related requests
    Extracts recipient email, subject, and body from user input and sends email

    Args:
        state: Dictionary containing 'input' key with user message

    Returns:
        state: Updated dictionary with 'output' key containing response
    """
    user_input = state.get("input", "").lower()

    # Extract email address using regex
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, state.get("input", ""))

    # Extract body/message content
    body = ""
    body_keywords = ["write", "message", "say", "body", "content", "text"]

    for keyword in body_keywords:
        if keyword in user_input:
            # Find text after the keyword
            parts = state.get("input", "").split(keyword, 1)
            if len(parts) > 1:
                body = parts[1].strip()
                # Remove quotes if present
                body = body.strip("\"'")
                break

    # Check what information we have
    if emails and body:
        recipient = emails[0]
        subject = "Message"

        # Actually send the email
        success, message = send_email(recipient, subject, body)
        state["output"] = message

    elif emails:
        recipient = emails[0]
        state["output"] = (
            f"I found the recipient: {recipient}\nWhat should I write in the email body?"
        )

    elif "send" in user_input or "email" in user_input:
        state["output"] = (
            "I can help you send an email. Please provide:\n1. Recipient email address\n2. Message content\n\nExample: 'send email to john@example.com write Hello there'"
        )
    else:
        state["output"] = "Email feature: I can help you send, read, or manage emails."

    return state
