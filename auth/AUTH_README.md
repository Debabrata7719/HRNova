# NovaHR Authentication System

## Overview

Simple login system added to NovaHR without modifying any existing code.

## Features

- ✅ Email/password authentication
- ✅ Role-based routing (HR vs Employee)
- ✅ Plain text passwords (for development)
- ✅ No external dependencies
- ✅ Zero breaking changes to existing code

## Database Structure

### Existing Table: `employees`

**New columns added:**
- `password` (VARCHAR(255)) - User password (plain text for now)
- `auth_role` (VARCHAR(20)) - User role: 'HR' or 'EMPLOYEE'

**Existing columns (unchanged):**
- `id` (INT) - Primary key
- `name` (VARCHAR(100)) - Employee name
- `email` (VARCHAR(100)) - Employee email
- `department` (VARCHAR(100)) - Department
- `role` (VARCHAR(100)) - Old field (ignored for auth)

## Setup Instructions

### Step 1: Add Authentication Columns

Run the setup script:

```bash
python setup_auth.py
```

This will:
1. Add `password` column to employees table
2. Add `auth_role` column to employees table
3. Set default credentials for all existing employees

**Default Credentials:**
- First employee: Role = HR, Password = `hr123`
- Other employees: Role = EMPLOYEE, Password = `emp123`

### Step 2: Verify Setup

Check your database:

```sql
SELECT id, name, email, auth_role, password FROM employees;
```

You should see the new columns populated.

### Step 3: Login

Run the authentication entry point:

```bash
python auth.py
```

Enter email and password when prompted.

## Usage

### Login Flow

```
$ python auth.py

============================================================
           NovaHR - AI-Powered HR Assistant
============================================================

Please login to continue:
Email: john@example.com
Password: hr123

Authenticating...

✓ Logged in as HR: John Doe
Launching HR Agent...
```

### Role-Based Routing

**If auth_role = 'HR':**
- Routes to `run_main_agent.py` (HR Agent)
- Full access to all features:
  - Leave management
  - Email sending
  - Policy queries
  - Meeting scheduling
  - General chat

**If auth_role = 'EMPLOYEE':**
- Routes to Employee Portal
- Limited access:
  - Apply for leave
  - Check leave balance
  - View leave status
  - Ask policy questions

## File Structure

```
NovaHR/
├── auth.py                  # Main authentication module
├── setup_auth.py            # Setup script for database
├── setup_auth.sql           # SQL script (alternative)
├── AUTH_README.md           # This file
│
└── src/
    └── tools/
        └── db_connection.py # Existing DB connection (reused)
```

## Code Overview

### 1. Database Connection

Uses existing `src/tools/db_connection.py`:

```python
from src.tools.db_connection import get_db

db = get_db()
result = db.execute_query(query, params)
```

### 2. Login Function

```python
def login(email: str, password: str) -> dict:
    """
    Authenticate user with email and password.
    
    Returns:
        {
            "success": bool,
            "message": str,
            "user": {
                "id": int,
                "name": str,
                "email": str,
                "department": str,
                "auth_role": str
            }
        }
    """
```

**Logic:**
1. Validate input (email and password required)
2. Query database for user by email
3. If user not found → return error
4. If password doesn't match → return error
5. If match → return user data

### 3. Role-Based Routing

```python
def route_to_agent(user: dict):
    """Route user to appropriate agent based on role."""
    
    if user["auth_role"] == "HR":
        # Launch HR Agent
        from run_main_agent import main as hr_main
        hr_main()
    
    elif user["auth_role"] == "EMPLOYEE":
        # Launch Employee Portal
        from src.main_agent.agents.employee.executor import run_employee_agent
        run_employee_agent()
```

### 4. Main Entry Point

```python
def main():
    """Main entry point with login loop."""
    
    # Allow 3 login attempts
    max_attempts = 3
    
    while attempts < max_attempts:
        email = input("Email: ")
        password = input("Password: ")
        
        result = login(email, password)
        
        if result["success"]:
            route_to_agent(result["user"])
            break
        else:
            print(f"Error: {result['message']}")
```

## Security Notes

### Current Implementation (Development)

- ❌ Plain text passwords
- ❌ No password hashing
- ❌ No session management
- ❌ No JWT tokens
- ❌ No rate limiting

### Before Production

**Must implement:**

1. **Password Hashing**
   ```python
   import bcrypt
   
   # Hash password
   hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
   
   # Verify password
   bcrypt.checkpw(password.encode(), hashed)
   ```

2. **Password Policies**
   - Minimum length (8+ characters)
   - Complexity requirements
   - Password expiration
   - Force change on first login

3. **Rate Limiting**
   - Limit login attempts per IP
   - Account lockout after failed attempts
   - CAPTCHA after multiple failures

4. **Session Management**
   - JWT tokens for API
   - Secure session cookies
   - Session timeout
   - Logout functionality

5. **Audit Logging**
   - Log all login attempts
   - Track failed logins
   - Monitor suspicious activity

## Testing

### Test Login Function

```python
from auth import login

# Test successful login
result = login("john@example.com", "hr123")
print(result)
# {
#     "success": True,
#     "message": "Login successful",
#     "user": {...}
# }

# Test invalid password
result = login("john@example.com", "wrong")
print(result)
# {
#     "success": False,
#     "message": "Invalid password",
#     "user": None
# }

# Test user not found
result = login("notfound@example.com", "password")
print(result)
# {
#     "success": False,
#     "message": "User not found",
#     "user": None
# }
```

### Test Role Routing

```bash
# Login as HR
python auth.py
# Email: hr@example.com
# Password: hr123
# → Should launch HR Agent (run_main_agent.py)

# Login as Employee
python auth.py
# Email: employee@example.com
# Password: emp123
# → Should launch Employee Portal
```

## Troubleshooting

### "User not found"

**Cause:** Email doesn't exist in database

**Solution:**
```sql
-- Check existing emails
SELECT email FROM employees;

-- Add new user
INSERT INTO employees (name, email, department, password, auth_role)
VALUES ('John Doe', 'john@example.com', 'IT', 'password123', 'EMPLOYEE');
```

### "Invalid password"

**Cause:** Password doesn't match

**Solution:**
```sql
-- Reset password
UPDATE employees 
SET password = 'newpassword' 
WHERE email = 'john@example.com';
```

### "Column 'password' doesn't exist"

**Cause:** Setup script not run

**Solution:**
```bash
python setup_auth.py
```

### "Unknown role"

**Cause:** auth_role is not 'HR' or 'EMPLOYEE'

**Solution:**
```sql
-- Fix role
UPDATE employees 
SET auth_role = 'EMPLOYEE' 
WHERE email = 'john@example.com';
```

## Examples

### Example 1: Add New HR User

```sql
INSERT INTO employees (name, email, department, password, auth_role)
VALUES ('Jane Smith', 'jane@example.com', 'HR', 'hr456', 'HR');
```

### Example 2: Change User Role

```sql
-- Promote employee to HR
UPDATE employees 
SET auth_role = 'HR' 
WHERE email = 'john@example.com';

-- Demote HR to employee
UPDATE employees 
SET auth_role = 'EMPLOYEE' 
WHERE email = 'jane@example.com';
```

### Example 3: Reset Password

```sql
UPDATE employees 
SET password = 'newpassword123' 
WHERE email = 'john@example.com';
```

### Example 4: List All Users

```sql
SELECT id, name, email, auth_role 
FROM employees 
ORDER BY auth_role, name;
```

## Migration Path

### Phase 1: Development (Current)
- ✅ Plain text passwords
- ✅ Simple email/password login
- ✅ Role-based routing

### Phase 2: Testing
- [ ] Add password hashing (bcrypt)
- [ ] Add password validation
- [ ] Add login attempt tracking

### Phase 3: Production
- [ ] Implement JWT tokens
- [ ] Add session management
- [ ] Add rate limiting
- [ ] Add audit logging
- [ ] Add password reset flow
- [ ] Add 2FA (optional)

## FAQ

**Q: Can I use this with the API?**  
A: Not yet. This is CLI-only. For API authentication, you'll need to add JWT tokens.

**Q: How do I change my password?**  
A: Currently via SQL only. Password change feature coming soon.

**Q: Can I have multiple HR users?**  
A: Yes! Just set `auth_role = 'HR'` for any employee.

**Q: What if I forget my password?**  
A: Contact administrator to reset via SQL.

**Q: Is this secure?**  
A: No! This is for development only. See "Security Notes" section.

## Support

For issues:
1. Check database connection: `python tests/test_connections.py`
2. Verify columns exist: `SELECT * FROM employees LIMIT 1;`
3. Check credentials in `.env` file
4. Review error messages in terminal

---

**Version:** 1.0.0  
**Last Updated:** May 4, 2026  
**Status:** Development Only - Not Production Ready
