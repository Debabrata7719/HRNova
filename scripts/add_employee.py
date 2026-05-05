"""
NovaHR - Add Employee Script
=============================
Run this script to add a new employee to the database.
Usage: python add_employee.py
"""

import sys
import os
import bcrypt

# Go up one level from scripts/ to project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.db_connection import get_db


def print_header():
    print()
    print("=" * 50)
    print("       NovaHR — Add New Employee")
    print("=" * 50)
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


def collect_employee_details():
    """Walk through all fields interactively."""

    print("Fill in the employee details below.")
    print("(Press Ctrl+C at any time to cancel)\n")

    # --- Name ---
    print("── Name")
    name = get_input("  Full name")

    # --- Email ---
    print("\n── Email")
    email = get_input("  Email address")
    # Basic format check
    if "@" not in email or "." not in email.split("@")[-1]:
        print(f"  ⚠ '{email}' doesn't look like a valid email, but continuing anyway.")

    # --- Department ---
    print("\n── Department")
    print("  Examples: Engineering, HR, Marketing, Finance, Operations, Sales")
    department = get_input("  Department")

    # --- Role ---
    print("\n── Role")
    role = get_role()

    # --- Password ---
    print("\n── Password  (used to log in to NovaHR)")
    password = get_password()

    return {
        "name": name,
        "email": email,
        "department": department,
        "role": role,
        "password": password,
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
    print(f"    Password   : {'*' * len(details['password'])}")
    print("─" * 50)
    print()
    answer = input("  Save this employee? [Y/n]: ").strip().lower()
    return answer in ("", "y", "yes")


def save_employee(db, details):
    """Hash password and insert into DB."""
    hashed = bcrypt.hashpw(
        details["password"].encode("utf-8"),
        bcrypt.gensalt(rounds=10)
    ).decode("utf-8")

    db.execute_query(
        """
        INSERT INTO employees (name, email, department, password, auth_role)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (details["name"], details["email"], details["department"], hashed, details["role"])
    )


def add_another():
    answer = input("\n  Add another employee? [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def main():
    print_header()

    # Connect to DB first — fail early if something is wrong
    try:
        db = get_db()
        if not db.connection or not db.connection.is_connected():
            print("✗ Could not connect to the database.")
            print("  Check your .env file (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).")
            sys.exit(1)
        print("✔ Connected to database\n")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)

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

        # Save
        try:
            save_employee(db, details)
            print(f"\n  ✔ Employee '{details['name']}' added successfully!")
            print(f"    They can log in with: {details['email']}")
        except Exception as e:
            print(f"\n  ✗ Failed to save: {e}")

        if not add_another():
            break

    print()
    print("=" * 50)
    print("  Done. Goodbye!")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
