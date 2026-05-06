"""
Simple Authentication Module for NovaHR
Handles login and role-based routing
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.db_connection import get_db
from src.config import get_settings
from src.logger import get_logger
import bcrypt
from jose import jwt
from datetime import datetime, timedelta

logger = get_logger(__name__)
_settings = get_settings()


def create_token(user: dict) -> str:
    """Create a JWT token for the authenticated user."""
    payload = {
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["auth_role"],
        "exp": datetime.utcnow() + timedelta(hours=_settings.TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, _settings.SECRET_KEY, algorithm=_settings.JWT_ALGORITHM)


def login(email: str, password: str) -> dict:
    """
    Authenticate user with email and password.
    
    Args:
        email: User's email address
        password: User's password (plain text)
    
    Returns:
        dict with:
            - success: bool (True if login successful)
            - message: str (error message or success message)
            - user: dict (user data if successful, None otherwise)
    """
    # Input validation
    if not email or not password:
        return {
            "success": False,
            "message": "Email and password are required",
            "user": None
        }
    
    # Get database connection
    db = get_db()
    
    # Query user by email
    query = """
        SELECT id, name, email, department, password, auth_role
        FROM employees
        WHERE email = %s
    """
    
    result = db.execute_query(query, (email,))
    
    # Check if user exists
    if not result or len(result) == 0:
        return {
            "success": False,
            "message": "User not found",
            "user": None
        }
    
    user_data = result[0]
    
    # Check password using bcrypt
    if not bcrypt.checkpw(password.encode('utf-8'), user_data["password"].encode('utf-8')):
        return {
            "success": False,
            "message": "Invalid password",
            "user": None
        }
    
    # Rehash with 10 rounds if stored hash uses more (transparent speed upgrade)
    # bcrypt hash format: $2b$<rounds>$<salt+hash>
    stored_hash = user_data["password"]
    try:
        current_rounds = int(stored_hash.split('$')[2])
        if current_rounds > 10:
            new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=10))
            db.execute_query(
                "UPDATE employees SET password=%s WHERE id=%s",
                (new_hash.decode('utf-8'), user_data["id"])
            )
    except Exception:
        pass  # If parsing fails, skip rehash — login still succeeds
    
    # Login successful - return user data (without password) + token
    user = {
        "id": user_data["id"],
        "name": user_data["name"],
        "email": user_data["email"],
        "department": user_data["department"],
        "auth_role": user_data["auth_role"]
    }
    return {
        "success": True,
        "message": "Login successful",
        "token": create_token(user),
        "user": user
    }


def route_to_agent(user: dict):
    auth_role = user.get("auth_role", "").upper()

    if auth_role == "HR":
        print(f"\n✓ Logged in as HR: {user['name']}")
        print("Launching HR Agent...\n")

        from run_main_agent import main as hr_main
        hr_main()

    elif auth_role == "EMPLOYEE":
        print(f"\n✓ Logged in as Employee: {user['name']}")
        print("Launching Employee Portal...\n")

        from src.main_agent.agents.employee.executor import run_employee_agent
        # Pass employee info so they don't need to enter name again
        run_employee_agent(
            employee_id=user['id'],
            employee_name=user['name'],
            employee_email=user['email']
        )

    else:
        print(f"\n✗ Error: Unknown role '{auth_role}'")


def main():
    """
    Main entry point for authenticated NovaHR system.
    Handles login and routes to appropriate agent.
    """
    print("=" * 60)
    print("           NovaHR - AI-Powered HR Assistant")
    print("=" * 60)
    print()
    
    # Login loop
    max_attempts = 3
    attempts = 0
    
    while attempts < max_attempts:
        print("Please login to continue:")
        
        # Get credentials
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        
        print("\nAuthenticating...")
        
        # Attempt login
        result = login(email, password)
        
        if result["success"]:
            # Login successful - route to agent
            route_to_agent(result["user"])
            break
        else:
            # Login failed
            attempts += 1
            remaining = max_attempts - attempts
            
            print(f"\n✗ {result['message']}")
            
            if remaining > 0:
                print(f"Attempts remaining: {remaining}\n")
            else:
                print("\nMaximum login attempts exceeded.")
                print("Please contact administrator for assistance.")
                break


if __name__ == "__main__":
    main()