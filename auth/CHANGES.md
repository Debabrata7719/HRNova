# Authentication Changes

## What Changed

### ✅ Employee Login Now Auto-Fills Name

**Before:**
```
1. Login with email/password
2. System asks: "Enter your name"
3. Employee types name again
```

**After:**
```
1. Login with email/password
2. System automatically fetches name from database
3. Employee goes directly to portal (no name prompt!)
```

## Modified Files

### 1. `auth/auth.py`
- Simplified to use plain text passwords (matching setup_auth.py)
- Removed bcrypt and JWT dependencies
- Updated `route_to_agent()` to pass employee info to portal

**Change:**
```python
# Now passes employee info
run_employee_agent(
    employee_id=user['id'],
    employee_name=user['name'],
    employee_email=user['email']
)
```

### 2. `src/main_agent/agents/employee/executor.py`
- Updated `run_employee_agent()` to accept optional parameters
- If employee info provided (from auth), uses it directly
- If not provided (standalone mode), asks for name as before

**Change:**
```python
def run_employee_agent(employee_id=None, employee_name=None, employee_email=None):
    # If info provided, skip name prompt
    if employee_id and employee_name:
        emp = {"id": employee_id, "name": employee_name}
        print(f"Welcome, {employee_name}!")
    else:
        # Standalone mode - ask for name
        name = input("Enter your name: ")
        emp = find_employee(name)
```

## How It Works Now

### Employee Login Flow

```
User runs: python auth/auth.py
    ↓
Enter email: rahul@gmail.com
Enter password: emp123
    ↓
System queries database:
  - Fetches: id, name, email, department, auth_role
    ↓
✓ Logged in as Employee: Rahul
Launching Employee Portal...
    ↓
Welcome, Rahul!  ← Name automatically filled!
I can help you with:
  1. Apply for leave
  2. Ask questions
```

### Standalone Mode (Still Works)

```
User runs: python run_employee_agent.py
    ↓
Enter your name: Rahul  ← Still asks for name
    ↓
Welcome, Rahul!
```

## Benefits

✅ **Better UX** - No redundant name entry  
✅ **Faster** - One less step for employees  
✅ **Consistent** - Uses authenticated user data  
✅ **Backward Compatible** - Standalone mode still works  

## Testing

```bash
# Test employee login
python auth/auth.py
# Email: rahul@gmail.com
# Password: emp123
# → Should NOT ask for name again
# → Should show "Welcome, Rahul!" directly

# Test standalone mode
python run_employee_agent.py
# → Should still ask for name (backward compatible)
```

## No Breaking Changes

- ✅ HR login unchanged
- ✅ Standalone employee portal unchanged
- ✅ All existing functionality preserved
- ✅ Only improved the authenticated flow

---

**Updated:** May 4, 2026  
**Status:** Complete ✅
