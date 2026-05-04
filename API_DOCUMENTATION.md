# NovaHR API Documentation

## Overview

The NovaHR API provides a RESTful interface to the AI-powered HR assistant. It supports chat-based interactions with session management, allowing frontend applications to integrate seamlessly.

**Base URL:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs` (Swagger UI)

**Alternative Docs:** `http://localhost:8000/redoc` (ReDoc)

## Features

- ✅ **No Authentication** - Simple API for development
- ✅ **Session Management** - In-memory session storage
- ✅ **CORS Enabled** - Ready for frontend integration
- ✅ **Auto-generated Docs** - Swagger UI and ReDoc
- ✅ **Type Safety** - Pydantic models for validation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
uvicorn api.main:app --reload --port 8000
```

### 3. Access Swagger UI

Open your browser: `http://localhost:8000/docs`

## Endpoints

### Health Check

#### `GET /`
Root endpoint - returns API status.

**Response:**
```json
{
  "status": "ok",
  "message": "NovaHR API is running",
  "version": "1.0.0"
}
```

#### `GET /health`
Health check endpoint - verifies API is healthy.

**Response:**
```json
{
  "status": "ok",
  "message": "NovaHR API is healthy",
  "version": "1.0.0"
}
```

---

### Chat Endpoints

#### `POST /api/chat`
Process a chat message and return the agent's response.

**Request Body:**
```json
{
  "message": "I want to apply for leave",
  "session_id": "user-session-123",
  "role": "hr",
  "employee_id": 0,
  "employee_name": ""
}
```

**Parameters:**
- `message` (string, required) - The user's message
- `session_id` (string, required) - Unique session identifier
- `role` (string, optional) - User role: "hr" or "employee" (default: "hr")
- `employee_id` (int, optional) - Employee ID (default: 0)
- `employee_name` (string, optional) - Employee name (default: "")

**Response:**
```json
{
  "response": "Hi! I'm here to help with your leave request. What's your name?",
  "session_id": "user-session-123",
  "intent": "leave_request",
  "step": "identify_employee"
}
```

**Status Codes:**
- `200` - Success
- `500` - Agent processing failed

---

#### `GET /api/chat/session/{session_id}`
Get information about a specific session.

**Parameters:**
- `session_id` (string, required) - The session ID to query

**Response (Session Exists):**
```json
{
  "session_id": "user-session-123",
  "intent": "leave_request",
  "step": "ask_leave_type",
  "exists": true
}
```

**Response (Session Not Found):**
```json
{
  "session_id": "user-session-123",
  "intent": null,
  "step": null,
  "exists": false
}
```

---

#### `DELETE /api/chat/session/{session_id}`
Delete a session and clear its state.

**Parameters:**
- `session_id` (string, required) - The session ID to delete

**Response (Success):**
```json
{
  "message": "Session cleared successfully"
}
```

**Response (Not Found):**
```json
{
  "message": "Session not found"
}
```

---

#### `GET /api/chat/sessions`
List all active sessions (for debugging/monitoring).

**Response:**
```json
{
  "total_sessions": 3,
  "session_ids": [
    "user-session-123",
    "user-session-456",
    "user-session-789"
  ]
}
```

---

## Usage Examples

### Example 1: Simple Chat Flow

```bash
# 1. Start a conversation
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "hello",
    "session_id": "demo-session",
    "role": "hr"
  }'

# Response:
# {
#   "response": "Hello! How can I help you today?",
#   "session_id": "demo-session",
#   "intent": "general",
#   "step": "completed"
# }

# 2. Check session status
curl "http://localhost:8000/api/chat/session/demo-session"

# 3. Clear session
curl -X DELETE "http://localhost:8000/api/chat/session/demo-session"
```

### Example 2: Leave Request Flow

```bash
# 1. Start leave request
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to apply for leave",
    "session_id": "leave-session",
    "role": "employee",
    "employee_id": 1,
    "employee_name": "John Doe"
  }'

# 2. Provide leave type
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "casual leave",
    "session_id": "leave-session",
    "role": "employee"
  }'

# 3. Continue conversation...
```

### Example 3: Policy Query

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "what is the leave policy?",
    "session_id": "policy-session",
    "role": "employee",
    "employee_id": 1,
    "employee_name": "Jane Smith"
  }'
```

---

## Session Management

### How Sessions Work

1. **Session Creation**: When a new `session_id` is sent, a fresh state is created
2. **State Persistence**: Each session maintains its own conversation state
3. **Memory**: Agent memories are preserved within the session
4. **Cleanup**: Sessions can be deleted manually via DELETE endpoint

### Session State

Each session stores:
- User input history
- Agent intent and step
- Leave/email/schedule data
- Agent memories (conversation history)
- Employee information

### Best Practices

1. **Generate Unique Session IDs**: Use UUIDs or timestamp-based IDs
2. **Clean Up Sessions**: Delete sessions when conversation ends
3. **Monitor Active Sessions**: Use `/api/chat/sessions` to track usage
4. **Handle Errors**: Wrap API calls in try-catch blocks

---

## Data Models

### ChatRequest

```python
{
  "message": str,           # Required
  "session_id": str,        # Required
  "role": str,              # Optional, default: "hr"
  "employee_id": int,       # Optional, default: 0
  "employee_name": str      # Optional, default: ""
}
```

### ChatResponse

```python
{
  "response": str,          # Agent's response
  "session_id": str,        # Session identifier
  "intent": str | None,     # Detected intent
  "step": str | None        # Current workflow step
}
```

### SessionInfo

```python
{
  "session_id": str,        # Session identifier
  "intent": str | None,     # Current intent
  "step": str | None,       # Current step
  "exists": bool            # Whether session exists
}
```

### HealthResponse

```python
{
  "status": str,            # "ok" or "error"
  "message": str,           # Status message
  "version": str            # API version
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Agent processing failed: <error message>"
}
```

### Common Errors

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input data |
| 422 | Validation Error - Pydantic validation failed |
| 500 | Internal Server Error - Agent processing failed |

---

## CORS Configuration

The API is configured to allow all origins for development:

```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

**Production Note:** Tighten CORS settings before deploying to production.

---

## Development

### Running in Development Mode

```bash
uvicorn api.main:app --reload --port 8000
```

### Running in Production Mode

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

The API uses the same `.env` file as the main application:

```env
GROQ_API_KEY=your_groq_api_key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=novahr
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=NovaHR
```

---

## Testing

### Manual Testing with Swagger UI

1. Open `http://localhost:8000/docs`
2. Click on any endpoint
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

### Automated Testing

```python
import requests

# Test health endpoint
response = requests.get("http://localhost:8000/health")
assert response.status_code == 200
assert response.json()["status"] == "ok"

# Test chat endpoint
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "hello",
        "session_id": "test-123",
        "role": "hr"
    }
)
assert response.status_code == 200
assert "response" in response.json()
```

---

## Architecture

```
Frontend (React/Vue/etc)
    ↓
FastAPI (api/main.py)
    ↓
Chat Router (api/routers/chat.py)
    ↓
Session Manager (in-memory dict)
    ↓
NovaHR Agent (src/main_agent)
    ↓
LangGraph Pipeline
    ↓
Individual Agents (leave, email, query, etc)
```

---

## Future Enhancements

- [ ] Add authentication (JWT tokens)
- [ ] Add rate limiting
- [ ] Add request logging
- [ ] Add persistent session storage (Redis/PostgreSQL)
- [ ] Add WebSocket support for real-time chat
- [ ] Add file upload support
- [ ] Add admin endpoints
- [ ] Add metrics and monitoring

---

## Support

For issues or questions:
- Check Swagger UI: `http://localhost:8000/docs`
- Review logs in terminal
- Check session state: `GET /api/chat/session/{session_id}`

---

**Version:** 1.0.0  
**Last Updated:** May 4, 2026
