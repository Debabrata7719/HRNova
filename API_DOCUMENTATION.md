# NovaHR API Documentation

> Complete reference for the NovaHR FastAPI backend — authentication, chat, and session management.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Authentication Flow](#authentication-flow)
5. [API Endpoints](#api-endpoints)
   - [Health Check](#health-check)
   - [Login](#login)
   - [Chat](#chat)
   - [Session Management](#session-management)
6. [JWT Token](#jwt-token)
7. [Request & Response Models](#request--response-models)
8. [Error Codes](#error-codes)
9. [Frontend Integration Guide](#frontend-integration-guide)
10. [Environment Variables](#environment-variables)
11. [Running the Server](#running-the-server)
12. [Database Schema](#database-schema)

---

## Overview

NovaHR API is a FastAPI-based backend that exposes the NovaHR AI agent system over HTTP. It handles:

- **Authentication** — Email/password login with JWT token response
- **Chat** — Stateful conversation with the AI agent pipeline
- **Session Management** — Per-user session state stored in memory
- **Role-based routing** — HR and Employee roles handled automatically via token

**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`

---

## Architecture

```
Frontend
   │
   ├── POST /api/auth/login  ──→  auth/auth.py (bcrypt verify + JWT create)
   │        ↓
   │   Receives JWT token
   │
   └── POST /api/chat  ──→  Authorization: Bearer <token>
            │
            ├── api/dependencies/auth.py  (verify JWT)
            ├── api/routers/chat.py       (session management)
            └── src/main_agent/           (LangGraph pipeline)
                    ├── leave_agent
                    ├── email_agent
                    ├── query_agent
                    ├── schedule_agent
                    └── general_agent
```

---

## Project Structure

```
NovaHR/
├── api/
│   ├── __init__.py
│   ├── main.py                  ← FastAPI app, CORS, router registration
│   ├── models.py                ← Pydantic request/response models
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── auth.py              ← JWT verification dependency
│   └── routers/
│       ├── __init__.py
│       ├── auth.py              ← POST /api/auth/login
│       └── chat.py              ← POST /api/chat + session endpoints
│
├── auth/
│   ├── auth.py                  ← login(), create_token(), route_to_agent()
│   └── setup_auth.py            ← DB setup script (run once)
│
└── src/
    └── main_agent/              ← LangGraph agent pipeline
```

---

## Authentication Flow

```
1. User sends email + password
        ↓
2. auth.py queries MySQL employees table
        ↓
3. bcrypt.checkpw() verifies password against stored hash
        ↓
4. On success: create_token() generates JWT with user info
        ↓
5. Token returned to frontend (valid for 8 hours)
        ↓
6. Frontend sends token in every request header:
   Authorization: Bearer <token>
        ↓
7. get_current_user() dependency decodes token on each request
        ↓
8. user_id, name, role extracted and passed to agent
```

---

## API Endpoints

---

### Health Check

#### `GET /`
Returns API running status.

**No authentication required.**

**Response:**
```json
{
  "status": "ok",
  "message": "NovaHR API is running",
  "version": "1.0.0"
}
```

---

#### `GET /health`
Verifies API is healthy.

**No authentication required.**

**Response:**
```json
{
  "status": "ok",
  "message": "NovaHR API is healthy",
  "version": "1.0.0"
}
```

---

### Login

#### `POST /api/auth/login`

Authenticates a user and returns a JWT token.

**No authentication required.**

**Request Body:**
```json
{
  "email": "debu@gmail.com",
  "password": "721242"
}
```

**Success Response `200`:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "Debu",
    "email": "debu@gmail.com",
    "department": "Engineering",
    "auth_role": "HR"
  }
}
```

**Error Response `401`:**
```json
{
  "detail": "Invalid password"
}
```
```json
{
  "detail": "User not found"
}
```

**Token Expiry:** 8 hours from login time.

---

### Chat

#### `POST /api/chat`

Sends a message to the NovaHR AI agent and returns the response.

**Authentication required** — `Authorization: Bearer <token>`

The agent automatically uses the user's identity (name, ID, role) from the token. No need to pass employee info in the request body.

**Request Body:**
```json
{
  "message": "I want to apply for leave",
  "session_id": "user-123-session-1"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | The user's message to the agent |
| `session_id` | string | Unique ID to maintain conversation state. Generate one per user session. |

**Success Response `200`:**
```json
{
  "response": "What type of leave do you need? (EL, CL, or SL)",
  "session_id": "user-123-session-1",
  "intent": "leave_request",
  "step": "ask_leave_type"
}
```

| Field | Description |
|-------|-------------|
| `response` | Agent's reply to display to the user |
| `session_id` | Same session ID echoed back |
| `intent` | Current detected intent (leave_request, email_request, query_request, etc.) |
| `step` | Current step in the agent workflow |

**Error Response `401`:**
```json
{
  "detail": "Invalid or expired token"
}
```

**Error Response `500`:**
```json
{
  "detail": "Agent processing failed: <error details>"
}
```

**How the agent routes based on role:**
- `HR` role → Full agent (leave, email, query, schedule, general)
- `EMPLOYEE` role → Employee portal (leave + query only)

---

### Session Management

#### `GET /api/chat/session/{session_id}`

Get the current state of a session.

**Authentication required.**

**Response (session exists):**
```json
{
  "session_id": "user-123-session-1",
  "intent": "leave_request",
  "step": "ask_dates",
  "exists": true
}
```

**Response (session not found):**
```json
{
  "session_id": "user-123-session-1",
  "intent": null,
  "step": null,
  "exists": false
}
```

---

#### `DELETE /api/chat/session/{session_id}`

Clears a session and resets conversation state.

**Authentication required.**

**Response:**
```json
{
  "message": "Session cleared successfully"
}
```

Use this when the user logs out or starts a fresh conversation.

---

#### `GET /api/chat/sessions`

Lists all active sessions (for debugging/monitoring).

**Authentication required.**

**Response:**
```json
{
  "total_sessions": 3,
  "session_ids": ["user-1-session", "user-2-session", "user-3-session"]
}
```

---

## JWT Token

### Token Structure

The JWT token contains the following payload:

```json
{
  "user_id": 1,
  "name": "Debu",
  "email": "debu@gmail.com",
  "role": "HR",
  "exp": 1746450000
}
```

| Field | Description |
|-------|-------------|
| `user_id` | Employee ID from MySQL |
| `name` | Employee's full name |
| `email` | Employee's email |
| `role` | `HR` or `EMPLOYEE` |
| `exp` | Expiry timestamp (8 hours from login) |

### Algorithm
- **Algorithm:** HS256
- **Secret:** `SECRET_KEY` from `.env`
- **Expiry:** 8 hours

### Sending the Token

Include the token in every protected request:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Request & Response Models

### `LoginRequest`
```python
{
  "email": str,      # required
  "password": str    # required
}
```

### `ChatRequest`
```python
{
  "message": str,     # required — user's message
  "session_id": str   # required — unique session identifier
}
```

### `ChatResponse`
```python
{
  "response": str,          # agent's reply
  "session_id": str,        # echoed session ID
  "intent": str | null,     # detected intent
  "step": str | null        # current workflow step
}
```

### `SessionInfo`
```python
{
  "session_id": str,
  "intent": str | null,
  "step": str | null,
  "exists": bool
}
```

### `HealthResponse`
```python
{
  "status": str,       # "ok"
  "message": str,
  "version": str       # "1.0.0"
}
```

---

## Error Codes

| Code | Meaning | When |
|------|---------|------|
| `200` | Success | Request processed successfully |
| `401` | Unauthorized | Wrong credentials, missing/invalid/expired token |
| `500` | Server Error | Agent pipeline failed |

---

## Frontend Integration Guide

### Step 1 — Login and Store Token

```javascript
async function login(email, password) {
  const response = await fetch("http://localhost:8000/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail); // "Invalid password" or "User not found"
  }

  const data = await response.json();
  
  // Store token (use localStorage or sessionStorage)
  localStorage.setItem("token", data.token);
  localStorage.setItem("user", JSON.stringify(data.user));
  
  return data;
}
```

### Step 2 — Send Chat Messages

```javascript
async function sendMessage(message, sessionId) {
  const token = localStorage.getItem("token");

  const response = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId
    })
  });

  if (response.status === 401) {
    // Token expired — redirect to login
    localStorage.removeItem("token");
    window.location.href = "/login";
    return;
  }

  const data = await response.json();
  return data.response; // Display this to the user
}
```

### Step 3 — Clear Session on Logout

```javascript
async function logout(sessionId) {
  const token = localStorage.getItem("token");

  // Clear session on server
  await fetch(`http://localhost:8000/api/chat/session/${sessionId}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${token}` }
  });

  // Clear local storage
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  
  window.location.href = "/login";
}
```

### Step 4 — Generate a Session ID

```javascript
// Generate a unique session ID per user session
function generateSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Or use user ID + timestamp for consistency
function getUserSessionId(userId) {
  return `user-${userId}-${Date.now()}`;
}
```

### Complete Example Flow

```javascript
// 1. Login
const { token, user } = await login("rahul@gmail.com", "123");

// 2. Generate session ID
const sessionId = generateSessionId();

// 3. Chat loop
const reply1 = await sendMessage("I want to apply for leave", sessionId);
// → "What type of leave do you need? (EL, CL, or SL)"

const reply2 = await sendMessage("CL", sessionId);
// → "Got it, CL. When do you want to take leave?"

const reply3 = await sendMessage("2026-05-10 to 2026-05-12", sessionId);
// → "I see, 3 days from 2026-05-10 to 2026-05-12. Any reason for this leave?"

// 4. Logout
await logout(sessionId);
```

---

## Environment Variables

Add these to your `.env` file:

```env
# JWT Authentication
SECRET_KEY=novahr_super_secret_key_2026

# MySQL Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=novahr

# Groq LLM
GROQ_API_KEY=your_groq_api_key

# LangSmith (optional)
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=novahr
```

> **Important:** Change `SECRET_KEY` to a strong random string before deploying to production.

---

## Running the Server

### Development (with auto-reload)
```bash
uvicorn api.main:app --reload --port 8000
```

### Production
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Database Schema

### `employees` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT (PK) | Employee ID |
| `name` | VARCHAR | Full name |
| `email` | VARCHAR | Login email |
| `department` | VARCHAR | Department name |
| `password` | VARCHAR(255) | bcrypt hashed password |
| `auth_role` | VARCHAR(20) | `HR` or `EMPLOYEE` |

### `leaves` table

| Column | Type | Description |
|--------|------|-------------|
| `leave_id` | INT (PK) | Leave request ID |
| `employee_id` | INT (FK) | References employees.id |
| `leave_type` | VARCHAR | `EL`, `CL`, or `SL` |
| `start_date` | DATE | Leave start date |
| `end_date` | DATE | Leave end date |
| `days` | INT | Number of days |
| `status` | VARCHAR(20) | `pending`, `approved`, `rejected` |
| `reason` | TEXT | Reason for leave |
| `submitted_at` | TIMESTAMP | Submission timestamp |

### Leave Policy

| Type | Full Name | Days/Year |
|------|-----------|-----------|
| `EL` | Earned Leave | 18 |
| `CL` | Casual Leave | 12 |
| `SL` | Sick Leave | 12 |

---

## Default Credentials (Development)

| Name | Email | Password | Role |
|------|-------|----------|------|
| Debu | debu@gmail.com | 721242 | HR |
| Rahul | rahul@gmail.com | 123 | EMPLOYEE |
| Priya | priya@gmail.com | 123 | EMPLOYEE |

> These are development credentials. Change passwords before going to production.
