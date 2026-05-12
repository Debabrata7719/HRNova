"""
Employee Management Router
POST /api/employees — Add a new employee (HR only)
Auto-generates password, inserts to DB, then sends welcome email.
Email is ONLY sent after successful DB insertion.
"""

import random
import bcrypt
import yagmail
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.dependencies.auth import get_current_user
from src.tools.db_connection import get_db
from src.config import get_settings
from src.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class AddEmployeeRequest(BaseModel):
    name: str
    email: str
    department: str
    role: str = "EMPLOYEE"


def generate_password(name: str) -> str:
    """
    Generate password: First4LettersOfCleanName + @ + 4 random digits
    "raj kumar" -> "Rajk@4821"
    "Ali"       -> "Ali@3392"
    """
    clean_name = "".join(name.split()).title()
    prefix = clean_name[:4] if len(clean_name) >= 4 else clean_name
    digits = str(random.randint(1000, 9999))
    return f"{prefix}@{digits}"


def send_welcome_email(employee_name: str, employee_email: str, password: str) -> bool:
    """
    Send welcome email with credentials.
    Called ONLY after successful DB insertion.
    Returns True on success, False on failure (non-fatal).
    """
    cfg = get_settings()

    if not cfg.EMAIL_ADDRESS or not cfg.EMAIL_APP_PASSWORD:
        logger.warning("[EMPLOYEE] Email not configured — skipping welcome email")
        return False

    subject = "Welcome to NovaHR — Your Account is Ready"
    body = f"""Hello {employee_name},

Your NovaHR account has been created by HR.

Your login credentials:
  Email    : {employee_email}
  Password : {password}

Please log in and change your password after your first login.
This is a system generated email, don't reply to it.

— NovaHR HR Team"""

    try:
        yag = yagmail.SMTP(
            user=cfg.EMAIL_ADDRESS,
            password=cfg.EMAIL_APP_PASSWORD,
        )
        yag.send(to=employee_email, subject=subject, contents=body)
        logger.info("[EMPLOYEE] Welcome email sent to %s", employee_email)
        return True
    except Exception as e:
        logger.error("[EMPLOYEE] Failed to send welcome email to %s: %s", employee_email, e)
        return False


@router.post("/employees")
def add_employee(request: AddEmployeeRequest, user=Depends(get_current_user)):
    """
    Add a new employee. HR only.

    Order of operations:
    1. Validate inputs
    2. Check email not duplicate
    3. Generate password
    4. Hash password
    5. INSERT into DB  — if this fails, raise error, NO email sent
    6. Send welcome email (best-effort, after successful insert only)
    7. Return employee data + generated password
    """
    if user.get("role") != "HR":
        raise HTTPException(status_code=403, detail="Only HR can add employees")

    role = request.role.upper()
    if role not in ("EMPLOYEE", "HR"):
        raise HTTPException(status_code=400, detail="Role must be EMPLOYEE or HR")

    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    email = request.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")

    department = request.department.strip()
    if not department:
        raise HTTPException(status_code=400, detail="Department is required")

    db = get_db()

    # Check duplicate
    existing = db.execute_query(
        "SELECT id FROM employees WHERE email = %s", (email,)
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Email '{email}' is already registered"
        )

    # Generate + hash password
    password = generate_password(name)
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=10)
    ).decode("utf-8")

    # DB insertion — email NOT sent before this
    new_id = db.insert_query(
        """
        INSERT INTO employees (name, email, department, password, auth_role)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (name, email, department, hashed, role)
    )

    if new_id is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to insert employee into database"
        )

    logger.info("[EMPLOYEE] Added: %s (%s) id=%s", name, email, new_id)

    # Send welcome email ONLY after successful DB insert
    email_sent = send_welcome_email(name, email, password)

    return {
        "success": True,
        "employee": {
            "id": new_id,
            "name": name,
            "email": email,
            "department": department,
            "role": role,
        },
        "generated_password": password,
        "email_sent": email_sent,
        "message": (
            f"Employee '{name}' added successfully. "
            + ("Credentials emailed to the employee."
               if email_sent
               else "Email could not be sent — share the password manually.")
        )
    }
