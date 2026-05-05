"""
Setup Authentication for NovaHR (SAFE VERSION)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.db_connection import get_db
import bcrypt


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=10)).decode('utf-8')


def setup_auth_columns():
    db = get_db()

    print("\nSetting up authentication...\n")

    # ✅ Add columns safely
    try:
        db.execute_query("""
            ALTER TABLE employees 
            ADD COLUMN password VARCHAR(255)
        """)
        print("✔ password column added")
    except Exception as e:
        print("ℹ password column already exists")

    try:
        db.execute_query("""
            ALTER TABLE employees 
            ADD COLUMN auth_role VARCHAR(20)
        """)
        print("✔ auth_role column added")
    except Exception as e:
        print("ℹ auth_role column already exists")

    # ✅ Fetch users
    employees = db.execute_query("SELECT id, name, email, password FROM employees")

    for i, emp in enumerate(employees, 1):

        # 👉 Skip if already hashed
        if emp["password"] and emp["password"].startswith("$2b$"):
            print(f"{emp['name']} → already configured")
            continue

        if i == 1:
            role = "HR"
            raw_password = "721242"
        else:
            role = "EMPLOYEE"
            raw_password = "123"

        hashed_password = hash_password(raw_password)

        db.execute_query("""
            UPDATE employees 
            SET password=%s, auth_role=%s 
            WHERE id=%s
        """, (hashed_password, role, emp["id"]))

        print(f"{emp['name']} → {role} (updated)")

    print("\n✅ Setup complete (passwords hashed)\n")


if __name__ == "__main__":
    setup_auth_columns()