"""
NovaHR - Employee Management Script
====================================
Run this script to:
1. Add a new employee to the database
2. Reset an employee's password

Usage: python add_employee.py
"""

import sys
import os
import bcrypt
import random
import yagmail

# Go up one level from scripts/ to project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.db_connection import get_db
from src.config import get_settings


def generate_password(name: str) -> str:
    """Generate password: First4LettersOfCleanName + @ + 4 random digits"""
    clean_name = "".join(name.split()).title()
    prefix = clean_name[:4] if len(clean_name) >= 4 else clean_name
    digits = str(random.randint(1000, 9999))
    return f"{prefix}@{digits}"


def send_welcome_email(employee_name: str, employee_email: str, password: str) -> bool:
    """Send welcome email after successful DB insertion."""
    cfg = get_settings()
    if not cfg.EMAIL_ADDRESS or not cfg.EMAIL_APP_PASSWORD:
        print("  ⚠ Email not configured — skipping welcome email")
        return False
    try:
        yag = yagmail.SMTP(user=cfg.EMAIL_ADDRESS, password=cfg.EMAIL_APP_PASSWORD)
        subject = "Welcome to NovaHR — Your Account is Ready"
        body = f"""Hello {employee_name},

Your NovaHR account has been created by HR.

Your login credentials:
  Email    : {employee_email}
  Password : {password}

Please log in and change your password after your first login.
This is a system generated email, don't reply to it.

— NovaHR HR Team"""
        yag.send(to=employee_email, subject=subject, contents=body)
        return True
    except Exception as e:
        print(f"  ⚠ Could not send email: {e}")
        return False


def print_header():
    print()
    print("=" * 50)
    print("       NovaHR — Employee Management")
    print("=" * 50)
    print()


def print_menu():
    """Display main menu."""
    print("\nWhat would you like to do?")
    print("  1. Add new employee")
    print("  2. Exit")
    print()


def get_input(prompt, required=True, default=None):
    """Ask for input, re-prompt if required field is empty."""
    while True:
        display = f"{prompt} [{default}]: " if default else f"{prompt}: "
        value = input(display).strip()
        if not value and default:
            return default
        if not value and required:
            print(f"  ✗ This field is required. Please enter a value.\n")
            continue
        return value


def get_role():
    """Ask for role with validation."""
    while True:
        print("  Role options:")
        print("    1. EMPLOYEE")
        print("    2. HR")
        choice = input("  Choose role [1/2] (default: 1): ").strip()
        if choice in ("", "1"):
            return "EMPLOYEE"
        elif choice == "2":
            return "HR"
        else:
            print("  ✗ Please enter 1 or 2.\n")


def get_password():
    """Ask for password twice to confirm."""
    while True:
        password = input("  Password: ").strip()
        if not password:
            print("  ✗ Password cannot be empty.\n")
            continue
        if len(password) < 3:
            print("  ✗ Password must be at least 3 characters.\n")
            continue
        confirm = input("  Confirm password: ").strip()
        if password != confirm:
            print("  ✗ Passwords do not match. Try again.\n")
            continue
        return password


def email_exists(db, email):
    """Check if email is already registered."""
    result = db.execute_query(
        "SELECT id FROM employees WHERE email = %s", (email,)
    )
    return result and len(result) > 0


def find_employee(db, search_term):
    """Find employee by email or name."""
    # Try exact email match first
    result = db.execute_query(
        "SELECT id, name, email, department, auth_role FROM employees WHERE email = %s",
        (search_term,)
    )
    if result:
        return result[0]
    
    # Try name match (partial)
    result = db.execute_query(
        "SELECT id, name, email, department, auth_role FROM employees WHERE LOWER(name) LIKE %s",
        (f"%{search_term.lower()}%",)
    )
    if result:
        if len(result) == 1:
            return result[0]
        else:
            # Multiple matches - show list
            print(f"\n  Found {len(result)} employees matching '{search_term}':")
            for i, emp in enumerate(result, 1):
                print(f"    {i}. {emp['name']} ({emp['email']})")
            
            while True:
                choice = input(f"\n  Select employee [1-{len(result)}]: ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(result):
                        return result[idx]
                    else:
                        print(f"  ✗ Please enter a number between 1 and {len(result)}")
                except ValueError:
                    print("  ✗ Please enter a valid number")
    
    return None


def collect_employee_details():
    """Walk through all fields interactively. Password is auto-generated."""

    print("Fill in the employee details below.")
    print("(Press Ctrl+C at any time to cancel)\n")

    print("── Name")
    name = get_input("  Full name")

    print("\n── Email")
    email = get_input("  Email address")
    if "@" not in email or "." not in email.split("@")[-1]:
        print(f"  ⚠ '{email}' doesn't look like a valid email, but continuing anyway.")

    print("\n── Department")
    print("  Examples: Engineering, HR, Marketing, Finance, Operations, Sales")
    department = get_input("  Department")

    print("\n── Role")
    role = get_role()

    return {
        "name": name,
        "email": email,
        "department": department,
        "role": role,
    }


def confirm_details(details):
    """Show a summary and ask for confirmation."""
    print()
    print("─" * 50)
    print("  Review before saving:")
    print(f"    Name       : {details['name']}")
    print(f"    Email      : {details['email']}")
    print(f"    Department : {details['department']}")
    print(f"    Role       : {details['role']}")
    print(f"    Password   : auto-generated")
    print("─" * 50)
    print()
    answer = input("  Save this employee? [Y/n]: ").strip().lower()
    return answer in ("", "y", "yes")


def save_employee(db, details):
    """Generate password, hash it, insert into DB, then send welcome email."""
    password = generate_password(details["name"])
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=10)
    ).decode("utf-8")

    db.execute_query(
        """
        INSERT INTO employees (name, email, department, password, auth_role)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (details["name"], details["email"], details["department"], hashed, details["role"])
    )
    return password


def reset_password_workflow(db):
    """Reset password for an existing employee."""
    print()
    print("=" * 50)
    print("       Reset Employee Password")
    print("=" * 50)
    print()
    
    # Search for employee
    search = get_input("  Enter employee name or email")
    
    employee = find_employee(db, search)
    
    if not employee:
        print(f"\n  ✗ No employee found matching '{search}'")
        return
    
    # Show employee details
    print()
    print("─" * 50)
    print("  Employee found:")
    print(f"    Name       : {employee['name']}")
    print(f"    Email      : {employee['email']}")
    print(f"    Department : {employee['department']}")
    print(f"    Role       : {employee['auth_role']}")
    print("─" * 50)
    print()
    
    # Confirm
    answer = input("  Reset password for this employee? [Y/n]: ").strip().lower()
    if answer not in ("", "y", "yes"):
        print("  Cancelled.")
        return
    
    # Get new password
    print("\n── New Password")
    new_password = get_password()
    
    # Hash and update
    try:
        hashed = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(rounds=10)
        ).decode("utf-8")
        
        db.execute_query(
            "UPDATE employees SET password = %s WHERE id = %s",
            (hashed, employee['id'])
        )
        
        print(f"\n  ✔ Password reset successfully for '{employee['name']}'!")
        print(f"    They can now log in with: {employee['email']}")
        print(f"    New password: {'*' * len(new_password)}")
    except Exception as e:
        print(f"\n  ✗ Failed to reset password: {e}")


def add_employee_workflow(db):
    """Add a new employee."""
    print()
    print("=" * 50)
    print("       Add New Employee")
    print("=" * 50)
    print()
    
    while True:
        try:
            details = collect_employee_details()
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            break

        # Check duplicate email
        if email_exists(db, details["email"]):
            print(f"\n  ✗ Email '{details['email']}' is already registered. Try a different email.\n")
            continue

        # Confirm before saving
        if not confirm_details(details):
            print("  Discarded. Starting over...\n")
            continue

        # Save — returns the generated password
        try:
            password = save_employee(db, details)
            print(f"\n  ✔ Employee '{details['name']}' added successfully!")
            print(f"    Login email : {details['email']}")
            print(f"    Password    : {password}  ← save this, shown only once")

            # Send welcome email ONLY after successful DB insert
            print("\n  Sending welcome email...")
            sent = send_welcome_email(details["name"], details["email"], password)
            if sent:
                print("  ✔ Welcome email sent to employee.")
            else:
                print("  ⚠ Email not sent — share the password manually.")
        except Exception as e:
            print(f"\n  ✗ Failed to save: {e}")

        # Ask if want to add another
        answer = input("\n  Add another employee? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            break


def main():
    print_header()

    # Connect to DB first — fail early if something is wrong
    try:
        db = get_db()
        if not db.connection or not db.connection.is_connected():
            print("✗ Could not connect to the database.")
            print("  Check your .env file (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).")
            sys.exit(1)
        print("✔ Connected to database")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)

    while True:
        print_menu()
        choice = input("  Enter your choice [1-2]: ").strip()

        if choice == "1":
            add_employee_workflow(db)
        elif choice == "2":
            print("\n  Goodbye!")
            break
        else:
            print("\n  ✗ Invalid choice. Please enter 1 or 2.")

    print()
    print("=" * 50)
    print("  Done. Goodbye!")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
