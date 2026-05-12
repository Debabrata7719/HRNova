# NovaHR API Documentation

> Base URL: `http://localhost:8000`
> Interactive docs: `http://localhost:8000/docs`
> ReDoc: `http://localhost:8000/redoc`

---

## Authentication

All protected endpoints require a **Bearer JWT token** in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are obtained from `POST /api/auth/login` and expire after **8 hours**.

---

## Response Format

All responses are JSON. Errors follow this structure:

```json
{
  "detail": "Error message here"
}
```

---

## Endpoints

### Health

#### `GET /`
Check if the API is running.

**Auth:** Not required

**Response `200`:**
```json
{
  "status": "ok",
  "message": "NovaHR API is running",
  "version": "1.0.0"
}
```

---

#### `GET /health`
Health check endpoint.

**Auth:** Not required

**Response `200`:**
```json
{
  "status": "ok",
  "message": "NovaHR API is healthy",
  "version": "1.0.0"
}
```

---

### Auth — `/api/auth`

#### `POST /api/auth/login`
Authenticate a user and receive a JWT token.

**Auth:** Not required

**Request body:**
```json
{
  "email": "debabratadey9090@gmail.com",
  "password": "721242"
}
```

**Response `200`:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "Debabrata Dey",
    "email": "debabratadey9090@gmail.com",
    "department": "HR",
    "auth_role": "HR"
  }
}
```

**Response `401`** — Invalid credentials:
```json
{
  "detail": "Invalid password"
}
```

**Response `422`** — Missing fields:
```json
{
  "detail": [{ "msg": "field required", "loc": ["body", "email"] }]
}
```

---

### Chat — `/api`

#### `POST /api/chat`
Send a message to the AI agent and receive a response.

**Auth:** Required (any role)

**Request body:**
```json
{
  "message": "What is my leave balance?",
  "session_id": "session-1234567890-abc123"
}
```

**Response `200`:**
```json
{
  "response": "Your Leave Balance:\n  EL (Earned): 5 used, 13 remaining out of 18\n  CL (Casual): 0 used, 12 remaining out of 12\n  SL (Sick): 0 used, 12 remaining out of 12",
  "session_id": "session-1234567890-abc123",
  "intent": "query_request",
  "step": "completed"
}
```

**Response `401`** — Invalid/expired token

**Response `500`** — Agent processing failed

**Notes:**
- The `session_id` maintains conversation context across multiple messages
- Generate a unique session ID per conversation (e.g. `session-{timestamp}-{random}`)
- The agent automatically retrieves long-term memory and stores important facts
- `intent` values: `leave_request`, `email_request`, `query_request`, `schedule_request`, `general`
- `step` values: `initial`, `identify_employee`, `ask_leave_type`, `ask_dates`, `ask_reason`, `confirm_request`, `completed`, `error`

---

#### `GET /api/chat/session/{session_id}`
Get the current state of a chat session.

**Auth:** Required (any role)

**Path params:**
- `session_id` — The session ID to query

**Response `200` (session exists):**
```json
{
  "session_id": "session-1234567890-abc123",
  "intent": "leave_request",
  "step": "ask_dates",
  "exists": true
}
```

**Response `200` (session not found):**
```json
{
  "session_id": "session-1234567890-abc123",
  "intent": null,
  "step": null,
  "exists": false
}
```

---

#### `DELETE /api/chat/session/{session_id}`
Clear a chat session and reset its state.

**Auth:** Required (any role)

**Path params:**
- `session_id` — The session ID to delete

**Response `200`:**
```json
{
  "message": "Session cleared successfully"
}
```

**Response `200`** (if session didn't exist):
```json
{
  "message": "Session not found"
}
```

---

#### `GET /api/chat/sessions`
List all active sessions (for debugging/monitoring).

**Auth:** Required (any role)

**Response `200`:**
```json
{
  "total_sessions": 3,
  "session_ids": [
    "session-1234567890-abc123",
    "session-9876543210-xyz789"
  ]
}
```

---

### Leaves — `/api`

#### `GET /api/leaves/stats`
Get leave request statistics (counts by status).

**Auth:** Required — **HR only**

**Response `200`:**
```json
{
  "total": 15,
  "pending": 3,
  "approved": 10,
  "rejected": 2
}
```

**Response `403`** — Not HR role

---

#### `GET /api/leaves`
Get all leave requests with employee details, ordered by most recent.

**Auth:** Required — **HR only**

**Response `200`:**
```json
[
  {
    "leave_id": 12,
    "name": "Sayandip Bar",
    "email": "sayandip05@gmail.com",
    "leave_type": "CL",
    "start_date": "2026-05-10",
    "end_date": "2026-05-12",
    "days": 3,
    "status": "pending",
    "reason": "Personal work",
    "submitted_at": "2026-05-07 10:30:00"
  }
]
```

**Leave type values:** `EL` (Earned Leave), `CL` (Casual Leave), `SL` (Sick Leave)

**Status values:** `pending`, `approved`, `rejected`

**Response `403`** — Not HR role

**Response `500`** — Database error

---

#### `PUT /api/leaves/{leave_id}/approve`
Approve a leave request by ID.

**Auth:** Required — **HR only**

**Path params:**
- `leave_id` — Integer ID of the leave request

**Response `200`:**
```json
{
  "message": "Leave approved successfully"
}
```

**Response `200`** (already approved):
```json
{
  "message": "Leave is already approved"
}
```

**Response `403`** — Not HR role

**Response `404`** — Leave request not found

---

#### `PUT /api/leaves/{leave_id}/reject`
Reject a leave request by ID.

**Auth:** Required — **HR only**

**Path params:**
- `leave_id` — Integer ID of the leave request

**Response `200`:**
```json
{
  "message": "Leave rejected successfully"
}
```

**Response `200`** (already rejected):
```json
{
  "message": "Leave is already rejected"
}
```

**Response `403`** — Not HR role

**Response `404`** — Leave request not found

---

### Memory — `/api`

#### `GET /api/memory/stats`
Get total memory count across all users.

**Auth:** Required (any role)

**Response `200`:**
```json
{
  "total_memories": 42,
  "collection_name": "novahr_long_term_memory"
}
```

---

#### `GET /api/memory/user`
Get all stored memories for the currently authenticated user.

**Auth:** Required (any role — users see only their own memories)

**Response `200`:**
```json
{
  "user_id": "1",
  "total_memories": 5,
  "memories": [
    {
      "text": "My name is Debu and I work in Engineering",
      "timestamp": "2026-05-06T10:30:00.123456",
      "intent": "general",
      "type": "user_input"
    }
  ]
}
```

---

#### `DELETE /api/memory/user`
Clear all memories for the currently authenticated user.

**Auth:** Required (any role)

**Response `200`:**
```json
{
  "message": "All memories cleared for user 1",
  "user_id": "1"
}
```

---

#### `GET /api/memory/all`
Get memories for ALL users grouped by user ID.

**Auth:** Required — **HR only**

**Response `200`:**
```json
{
  "total_memories": 42,
  "total_users": 2,
  "memories_by_user": {
    "1": [
      {
        "text": "My name is Debu",
        "timestamp": "2026-05-06T10:30:00",
        "intent": "general",
        "type": "user_input"
      }
    ],
    "2": [
      {
        "text": "I prefer casual leave on Fridays",
        "timestamp": "2026-05-05T14:20:00",
        "intent": "leave_request",
        "type": "user_input"
      }
    ]
  }
}
```

**Response `403`** — Not HR role

---

#### `DELETE /api/memory/user/{user_id}`
Clear all memories for a specific user.

**Auth:** Required — **HR only**

**Path params:**
- `user_id` — Integer employee ID

**Response `200`:**
```json
{
  "message": "All memories cleared for user 2",
  "user_id": 2
}
```

**Response `403`** — Not HR role

---

#### `POST /api/memory/cleanup`
Delete memories older than a specified number of days.

**Auth:** Required — **HR only**

**Request body:**
```json
{
  "days": 30
}
```

**Special values:**
- `days: 0` — Delete ALL memories regardless of age
- `days: 1` — Delete anything before today (midnight)
- `days: 30` — Delete anything older than 30 days (default)

**Response `200`:**
```json
{
  "message": "Deleted memories older than 30 days",
  "days": 30,
  "memories_before": 50,
  "memories_after": 42,
  "deleted": 8
}
```

**Response `403`** — Not HR role

---

#### `POST /api/memory/cleanup/trigger`
Trigger immediate cleanup using the default 30-day threshold.

**Auth:** Required — **HR only**

**Request body:** None required

**Response `200`:**
```json
{
  "message": "Cleanup triggered successfully",
  "days": 30,
  "memories_before": 50,
  "memories_after": 42,
  "deleted": 8
}
```

**Response `403`** — Not HR role

---

### Employees — `/api`

#### `POST /api/employees`
Add a new employee to the database. HR only.

Password is **auto-generated** using the format: `First4LettersOfCleanName@4Digits`

Examples:
- `"Raj Kumar"` → `Rajk@4821`
- `"Sayandip Bar"` → `Saya@3392`
- `"Ali"` → `Ali@7719`

**Auth:** Required — **HR only**

**Request body:**
```json
{
  "name": "Raj Kumar",
  "email": "raj@company.com",
  "department": "Engineering",
  "role": "EMPLOYEE"
}
```

**Role values:** `EMPLOYEE`, `HR`

**Response `200`:**
```json
{
  "success": true,
  "employee": {
    "id": 3,
    "name": "Raj Kumar",
    "email": "raj@company.com",
    "department": "Engineering",
    "role": "EMPLOYEE"
  },
  "generated_password": "Rajk@4821",
  "email_sent": true,
  "message": "Employee 'Raj Kumar' added successfully. Credentials emailed to the employee."
}
```

**Response `200`** (email failed — employee still created):
```json
{
  "success": true,
  "employee": { ... },
  "generated_password": "Rajk@4821",
  "email_sent": false,
  "message": "Employee 'Raj Kumar' added successfully. Email could not be sent — share the password manually."
}
```

**Response `400`** — Email already registered:
```json
{
  "detail": "Email 'raj@company.com' is already registered"
}
```

**Response `400`** — Invalid role:
```json
{
  "detail": "Role must be EMPLOYEE or HR"
}
```

**Response `403`** — Not HR role

**Response `422`** — Missing required fields

**Response `500`** — Database insertion failed (email is NOT sent in this case)

**Important rules:**
- Email is sent **only after** successful DB insertion — if DB fails, no email is sent
- The generated password is returned in the response and shown once to HR
- A welcome email is sent to the new employee's address with their login credentials

---

## Error Reference

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `401` | Missing, invalid or expired JWT token |
| `403` | Authenticated but insufficient role (HR required) |
| `404` | Resource not found |
| `422` | Request validation error (missing/wrong fields) |
| `500` | Internal server error (agent failure, DB error) |

---

## JWT Token Payload

The decoded JWT contains:

```json
{
  "user_id": 1,
  "name": "Debabrata Dey",
  "email": "debabratadey9090@gmail.com",
  "role": "HR",
  "exp": 1746700000
}
```

**Role values:** `HR`, `EMPLOYEE`

Token expires after **8 hours** from login.

---

## Background Jobs

The API runs an automatic background job:

| Job | Schedule | Action |
|-----|----------|--------|
| Memory Cleanup | Daily at 2:00 AM | Deletes memories older than 30 days |

---

## CORS

Currently configured to allow all origins (`*`). Restrict before production deployment:

```python
# api/main.py
allow_origins=["https://your-frontend-domain.com"]
```

---

## Running the API

```bash
python scripts/start_api.py
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
