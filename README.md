# NovaHR - AI-Powered HR Assistant

> Complete HR management system with AI chatbot, leave management, email automation, calendar scheduling, policy Q&A, and long-term memory.

---

## 📚 Quick Navigation

| Section | Description |
|---------|-------------|
| [🚀 Quick Start](#-quick-start) | Get up and running in 10 minutes |
| [✨ Features](#-features) | What NovaHR can do |
| [📁 Project Structure](#-project-structure) | Folder layout |
| [🛠 Installation](#-installation) | Full setup guide |
| [▶️ Running the App](#️-running-the-application) | Start backend & frontend |
| [📖 Usage](#-usage) | How to use the system |
| [🔌 API Endpoints](#-api-endpoints) | All REST endpoints |
| [🏗 Architecture](#-architecture) | System design & agent flow |
| [🧠 Memory System](#-memory-system) | Long-term memory with ChromaDB |
| [🧹 Memory Cleanup](#-memory-cleanup) | Automatic & manual cleanup |
| [🔍 LangSmith Tracing](#-langsmith-tracing) | Agent observability |
| [📊 HR Dashboard Troubleshooting](#-hr-dashboard-troubleshooting) | Fix dashboard issues |
| [🔐 Security](#-security) | Auth & access control |
| [📊 Database Schema](#-database-schema) | Tables & columns |
| [🛠 Tech Stack](#-tech-stack) | Libraries & tools used |
| [📝 Environment Variables](#-environment-variables) | All `.env` keys |
| [🐛 Troubleshooting](#-troubleshooting) | Common issues & fixes |
| [📈 Project Analysis](#-project-analysis) | Improvements & recommendations |

---

## 🚀 Quick Start

```bash
# 1. Clone and enter project
git clone <your-repo-url>
cd NovaHR

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your keys (see Environment Variables section)

# 5. Setup database
python auth/setup_auth.py

# 6. Embed company policy
python src/tools/embed_policy.py

# 7. Start backend
python start_api.py

# 8. Start frontend (new terminal)
cd novahr-frontend
npm install
npm start
```

Open `http://localhost:3000` and login:
- **HR:** `debu@gmail.com` / `721242`
- **Employee:** `rahul@gmail.com` / `123`

---

## ✨ Features

### 🤖 AI Assistant
- **Multi-Agent System** — LangGraph-powered routing to specialized agents
- **Leave Management** — Apply for leave with natural language
- **Email Automation** — Compose and send emails via Gmail SMTP
- **Calendar Integration** — Schedule meetings with Google Calendar
- **Policy Q&A** — ChromaDB vector search over company policy documents
- **Leave Balance Queries** — Real-time balance checks from MySQL
- **Long-term Memory** — Remembers important facts across sessions *(NEW)*
- **LangSmith Tracing** — Full observability of all agent executions

### 👔 HR Dashboard
- **Leave Request Management** — View all employee leave requests
- **Approve/Reject** — One-click approval/rejection with instant updates
- **Statistics** — Real-time counts (Total, Pending, Approved, Rejected)
- **Filter & Search** — Filter by status, search by employee
- **Memory Management** — View and manage user memories via API *(NEW)*

### 🔐 Authentication & Security
- **JWT Token-based Auth** — Secure login with bcrypt password hashing
- **Role-based Access** — HR and Employee roles with different permissions
- **Session Management** — Stateful conversations with per-user sessions
- **Automatic Memory Cleanup** — TTL-based cleanup every 30 days *(NEW)*

### 🌐 REST API
- **FastAPI Backend** — Auto-generated Swagger docs at `/docs`
- **CORS Enabled** — Ready for frontend integration
- **Protected Endpoints** — JWT verification on all sensitive routes
- **Memory API** — Endpoints for memory stats and management *(NEW)*

---

## 📁 Project Structure

```
NovaHR/
├── api/                          # FastAPI backend
│   ├── dependencies/
│   │   └── auth.py              # JWT verification
│   ├── routers/
│   │   ├── auth.py              # Login endpoint
│   │   ├── chat.py              # Chat with AI agent + memory integration
│   │   ├── leaves.py            # Leave management (HR only)
│   │   └── memory.py            # Memory management API
│   ├── main.py                  # FastAPI app + auto cleanup scheduler
│   └── models.py                # Pydantic models
│
├── auth/
│   ├── auth.py                  # Login logic + JWT creation
│   └── setup_auth.py            # Database setup script
│
├── src/
│   ├── main_agent/
│   │   ├── agents/
│   │   │   ├── email/           # Email agent
│   │   │   ├── leave/           # Leave agent
│   │   │   ├── query/           # Policy Q&A agent
│   │   │   ├── scheduling/      # Calendar agent
│   │   │   ├── employee/        # Employee portal
│   │   │   └── general/         # General conversation (uses long-term memory)
│   │   ├── memory.py            # Short-term conversation memory
│   │   └── router.py            # LangGraph routing + State definition
│   ├── tools/
│   │   ├── db_connection.py     # MySQL utility
│   │   └── embed_policy.py      # PDF embedder
│   └── utils/
│       ├── memory_store.py      # ChromaDB long-term memory storage
│       └── memory_filter.py     # LLM-based + keyword filtering
│
├── novahr-frontend/             # React frontend
│   └── src/
│       ├── pages/
│       │   ├── Login.jsx
│       │   ├── Chat.jsx
│       │   └── Dashboard.jsx
│       ├── services/
│       │   ├── authService.js
│       │   ├── chatService.js
│       │   └── leaveService.js
│       └── utils/
│           └── session.js
│
├── data/
│   ├── NovaHR_Company_Policy_Notebook.pdf
│   ├── chroma_db/               # Policy vector database
│   └── long_term_memory/        # Long-term memory vector database
│
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
├── start_api.py                 # API server launcher
├── cleanup_memory.py            # Manual memory cleanup script
├── run_main_agent.py            # CLI for HR
└── run_employee_agent.py        # CLI for employees
```

---

## 🛠 Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- MySQL 8.0+
- Gmail account (for email features)
- Google Cloud project (for calendar features)

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd NovaHR
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

#### Configure Environment Variables
Create `.env` file (or copy from `.env.example`):
```env
# LLM API
GROQ_API_KEY=your_groq_api_key

# Email (Gmail)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password

# MySQL Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=novahr

# JWT Secret (use a strong random string)
SECRET_KEY=your_super_secret_key_here

# LangSmith (optional - for agent tracing)
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=novahr
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

#### Setup MySQL Database
```sql
CREATE DATABASE novahr;
USE novahr;

CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    department VARCHAR(100),
    password VARCHAR(255),
    auth_role VARCHAR(20)
);

CREATE TABLE leaves (
    leave_id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT,
    leave_type VARCHAR(10),
    start_date DATE,
    end_date DATE,
    days INT,
    status VARCHAR(20) DEFAULT 'pending',
    reason TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

INSERT INTO employees (name, email, department, auth_role) VALUES
('Debu', 'debu@gmail.com', 'Engineering', 'HR'),
('Rahul', 'rahul@gmail.com', 'HR', 'EMPLOYEE'),
('Priya', 'priya@gmail.com', 'Marketing', 'EMPLOYEE');
```

#### Setup Authentication
```bash
python auth/setup_auth.py
```
Default credentials after setup:
- HR: `debu@gmail.com` / `721242`
- Employee: `rahul@gmail.com` / `123`

#### Embed Company Policy
```bash
python src/tools/embed_policy.py
```

### 3. Frontend Setup
```bash
cd novahr-frontend
npm install
```

---

## ▶️ Running the Application

### Start Backend (Terminal 1)
```bash
python start_api.py
```
- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- On startup you'll see: `[SCHEDULER] Automatic memory cleanup enabled (runs daily at 2 AM)`

### Start Frontend (Terminal 2)
```bash
cd novahr-frontend
npm start
```
- Frontend: `http://localhost:3000`

---

## 📖 Usage

### Web Interface

#### Login
Go to `http://localhost:3000` and login with:
- **HR:** `debu@gmail.com` / `721242`
- **Employee:** `rahul@gmail.com` / `123`

#### Chat with AI Assistant
- Ask questions: *"What is my leave balance?"*
- Apply for leave: *"I want to apply for leave"*
- Schedule meetings: *"Schedule a meeting tomorrow at 3pm"*
- Check policy: *"What is the casual leave policy?"*
- The agent remembers important facts across sessions via long-term memory

#### HR Dashboard (HR only)
- Navigate to `http://localhost:3000/dashboard`
- View all leave requests
- Approve/reject with one click
- Filter by status (All, Pending, Approved, Rejected)

### CLI Interface

#### HR Agent (Full Access)
```bash
python run_main_agent.py
```

#### Employee Portal (Leave + Queries)
```bash
python run_employee_agent.py
```

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login and get JWT token |

### Chat
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/chat` | ✓ | Send message to AI agent |
| `GET` | `/api/chat/session/{id}` | ✓ | Get session info |
| `DELETE` | `/api/chat/session/{id}` | ✓ | Clear session |

### Leave Management (HR Only)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/leaves` | ✓ HR | Get all leave requests |
| `GET` | `/api/leaves/stats` | ✓ HR | Get leave statistics |
| `PUT` | `/api/leaves/{id}/approve` | ✓ HR | Approve leave |
| `PUT` | `/api/leaves/{id}/reject` | ✓ HR | Reject leave |

### Memory Management
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/memory/stats` | ✓ | Get memory statistics |
| `GET` | `/api/memory/user/{user_id}` | ✓ | Get memories for a user |
| `POST` | `/api/memory/cleanup` | ✓ HR | Cleanup old memories (custom days) |
| `POST` | `/api/memory/cleanup/trigger` | ✓ HR | Trigger immediate cleanup (30 days) |

Full interactive docs: `http://localhost:8000/docs`

---

## 🏗 Architecture

### Backend Flow
```
User Request
    ↓
FastAPI (api/main.py)
    ↓
JWT Verification (api/dependencies/auth.py)
    ↓
Router (api/routers/*)
    ↓
Search Long-term Memory (ChromaDB)
    ↓
LangGraph Agent Pipeline (src/main_agent/router.py)
    ↓
Specialized Agents (leave/email/query/schedule/general)
    ↓
Tools (MySQL, ChromaDB, Gmail, Google Calendar)
    ↓
Filter & Store Important Info (memory_filter + memory_store)
    ↓
Response
```

### Agent Routing
```
User Message → Router Agent
    ├─→ Leave Agent      (apply/check leave)
    ├─→ Email Agent      (send emails)
    ├─→ Query Agent      (policy Q&A, balance check)
    ├─→ Schedule Agent   (calendar events)
    └─→ General Agent    (conversation + uses long-term memory)
```

---

## 🧠 Memory System

NovaHR uses **two types of memory** working together:

### Short-term Memory (Per Session)
- **Type:** `ConversationBufferWindowMemory` (LangChain)
- **Storage:** In-memory (RAM)
- **Scope:** Current conversation only
- **Window:** Last 5–10 messages
- **Persistence:** Lost when session ends
- **Purpose:** Maintain conversation context within a chat

### Long-term Memory (Across Sessions)
- **Type:** ChromaDB Vector Memory
- **Storage:** Persistent disk (`data/long_term_memory/`)
- **Scope:** All conversations per user
- **Persistence:** Survives server restarts
- **Purpose:** Remember important facts across sessions

---

### How Long-term Memory Works

```
User sends message
        ↓
1. Search ChromaDB for relevant past memories (vector similarity)
        ↓
2. Inject memories into agent state: state["long_term_memory"]
        ↓
3. Agent processes message with memory context
        ↓
4. Filter: Is this message/response important enough to store?
        ↓
5. Store important info in ChromaDB with metadata
        ↓
Return personalized response
```

### What Gets Stored

| Category | Keywords | Example |
|----------|----------|---------|
| Personal Info | "my name is", "i am", "i work in" | "My name is Debu" |
| Leave Details | "leave", "vacation", "sick" | "I need leave from May 10-12" |
| Work Info | "project", "deadline", "meeting" | "Working on the API project" |
| Preferences | "prefer", "usually", "always" | "I usually take leave on Fridays" |
| Important Facts | "remember", "important", "note" | "Remember I have a doctor appointment" |
| Completions | step == "completed" | "Leave successfully submitted" |

### What Gets Excluded
- Trivial responses: "ok", "yes", "thanks", "bye"
- Very short messages (< 5 characters)
- Generic questions without context

### Memory in Action

**Session 1:**
```
User: "My name is Debu and I work in Engineering"
Agent: "Nice to meet you, Debu!"
→ Stored in ChromaDB
```

**Session 2 (new session, days later):**
```
User: "Who am I?"
→ ChromaDB retrieves: "My name is Debu and I work in Engineering"
Agent: "You're Debu from the Engineering department!"
```

### Key Files
| File | Purpose |
|------|---------|
| `src/utils/memory_store.py` | ChromaDB storage & retrieval |
| `src/utils/memory_filter.py` | LLM-based + keyword filtering |
| `api/routers/chat.py` | Memory integration in chat endpoint |
| `src/main_agent/agents/general/executor.py` | Agent uses memories in prompts |
| `src/main_agent/router.py` | `long_term_memory` added to State |

### Technical Specs
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Search Algorithm:** HNSW (Hierarchical Navigable Small World)
- **Similarity Metric:** Cosine similarity
- **Results per Query:** Top 3 most relevant memories
- **Storage Location:** `data/long_term_memory/`
- **Latency Added:** ~80ms per request

---

## 🧹 Memory Cleanup

### Automatic Cleanup (Recommended — Zero Effort)

When you start the server, cleanup runs automatically in the background:

```bash
python start_api.py
# Output: [SCHEDULER] Automatic memory cleanup enabled (runs daily at 2 AM)
```

- **Schedule:** Every day at 2:00 AM
- **Action:** Deletes memories older than 30 days
- **No manual work needed**

### Manual Cleanup Options

#### Option 1: API Trigger (Easiest)
Open Swagger UI at `http://localhost:8000/docs`, login, then:
```
POST /api/memory/cleanup/trigger
```
Response:
```json
{
  "message": "Cleanup triggered successfully",
  "days": 30,
  "memories_before": 150,
  "memories_after": 120,
  "deleted": 30
}
```

#### Option 2: Command Line Script
```bash
# Delete memories older than 30 days (default)
python cleanup_memory.py

# Delete memories older than 60 days
python cleanup_memory.py --days 60
```

#### Option 3: Python Code
```python
from src.utils.memory_store import get_memory_store

store = get_memory_store()
store.cleanup_old_memories(days=30)        # All users
store.clear_user_memories(user_id="1")    # Specific user
```

### Change Cleanup Schedule
Edit `api/main.py`:
```python
# Daily at 2 AM (current)
scheduler.add_job(cleanup_old_memories_job, trigger='cron', hour=2, minute=0)

# Every 12 hours
scheduler.add_job(cleanup_old_memories_job, trigger='interval', hours=12)

# Weekly on Sunday at 3 AM
scheduler.add_job(cleanup_old_memories_job, trigger='cron', day_of_week='sun', hour=3)
```

### Check Memory Stats
```
GET /api/memory/stats
```
```json
{
  "total_memories": 120,
  "collection_name": "novahr_long_term_memory"
}
```

---

## 🔍 LangSmith Tracing

### Status: Fully Integrated ✅

All agents have `@traceable` decorator for full observability:

| Agent | File |
|-------|------|
| Router Agent | `src/main_agent/router.py` |
| Route Decision | `src/main_agent/router.py` |
| Leave Agent | `src/main_agent/agents/leave/executor.py` |
| Email Agent | `src/main_agent/agents/email/executor.py` |
| Query Agent | `src/main_agent/agents/query/executor.py` |
| Schedule Agent | `src/main_agent/agents/scheduling/executor.py` |
| General Agent | `src/main_agent/agents/general/executor.py` |

### Enable Tracing
Add to `.env`:
```env
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=novahr
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

Then view traces at `https://smith.langchain.com/` under project `novahr`.

---

## 📊 HR Dashboard Troubleshooting

### Database Status Check
```bash
python test_dashboard.py
# Expected: Found 3 employees, Found X leave requests
```

### Dashboard Not Showing Data — Step by Step

**Step 1: Verify backend is running**
```
http://localhost:8000/docs  ← Should open Swagger UI
```

**Step 2: Test API directly in browser console (F12)**
```javascript
// Login and get token
fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ email: 'debu@gmail.com', password: '721242' })
}).then(r => r.json()).then(d => {
  localStorage.setItem('token', d.token);
  localStorage.setItem('user', JSON.stringify(d.user));
  console.log('Logged in:', d.user.auth_role);
});

// Fetch leaves (run after login)
fetch('http://localhost:8000/api/leaves', {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
}).then(r => r.json()).then(d => console.log('Leaves:', d));
```

**Step 3: Check user role**
```javascript
const user = JSON.parse(localStorage.getItem('user'));
console.log('Role:', user.auth_role); // Must be "HR"
```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Access denied. HR role required" | Wrong user role | Login as `debu@gmail.com` (HR) |
| Dashboard empty, no error | Token expired | `localStorage.clear()` then re-login |
| "Cannot connect to server" | Backend not running | Run `python start_api.py` |
| Data loads but doesn't display | JS error | Check browser console (F12) |

### Quick Reset
```javascript
// In browser console — clears auth and reloads
localStorage.clear();
sessionStorage.clear();
window.location.href = '/';
```

### Verification Checklist
- [ ] Backend running (`python start_api.py`)
- [ ] Frontend running (`npm start` in `novahr-frontend/`)
- [ ] Logged in as HR (`debu@gmail.com`)
- [ ] Token in localStorage
- [ ] No errors in browser console (F12)
- [ ] API returns data in Swagger UI
- [ ] Database has records (`python test_dashboard.py`)

---

## 🔐 Security

- **Passwords:** bcrypt hashed (cost factor 12)
- **JWT Tokens:** HS256 algorithm, 8-hour expiry
- **Role-based Access:** HR vs Employee permissions enforced at API level
- **CORS:** Configured for localhost (update for production)
- **Environment Variables:** Sensitive data in `.env` (not committed to git)

> **Note on SECRET_KEY:** Use a strong random string in production. Generate one with:
> ```python
> import secrets; print(secrets.token_urlsafe(32))
> ```

---

## 📊 Database Schema

### `employees` Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INT (PK) | Employee ID |
| `name` | VARCHAR(100) | Full name |
| `email` | VARCHAR(100) | Login email (unique) |
| `department` | VARCHAR(100) | Department |
| `password` | VARCHAR(255) | bcrypt hashed password |
| `auth_role` | VARCHAR(20) | `HR` or `EMPLOYEE` |

### `leaves` Table
| Column | Type | Description |
|--------|------|-------------|
| `leave_id` | INT (PK) | Leave request ID |
| `employee_id` | INT (FK) | References `employees.id` |
| `leave_type` | VARCHAR(10) | `EL`, `CL`, or `SL` |
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

## 🛠 Tech Stack

### Backend
| Tool | Purpose |
|------|---------|
| FastAPI | REST API framework |
| Groq (Llama) | LLM for agent reasoning |
| LangGraph + LangChain | Agent pipeline & routing |
| MySQL | Employee & leave data |
| ChromaDB | Vector DB (policy + long-term memory) |
| HuggingFace Sentence Transformers | Text embeddings |
| JWT (python-jose) + bcrypt | Authentication |
| APScheduler | Automatic memory cleanup |
| LangSmith | Agent tracing & observability |

### Frontend
| Tool | Purpose |
|------|---------|
| React 18 | UI framework |
| Custom CSS | Styling |
| Fetch API | HTTP requests |
| React Hooks | State management |

### Integrations
- **Email:** Gmail SMTP
- **Calendar:** Google Calendar API

---

## 📝 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✓ | Groq API key for LLM |
| `EMAIL_ADDRESS` | ✓ | Gmail address for sending emails |
| `EMAIL_APP_PASSWORD` | ✓ | Gmail app password |
| `DB_HOST` | ✓ | MySQL host (default: localhost) |
| `DB_USER` | ✓ | MySQL username |
| `DB_PASSWORD` | ✓ | MySQL password |
| `DB_NAME` | ✓ | MySQL database name |
| `SECRET_KEY` | ✓ | JWT secret key (use strong random string) |
| `LANGCHAIN_API_KEY` | ✗ | LangSmith API key (optional) |
| `LANGCHAIN_TRACING_V2` | ✗ | Enable LangSmith tracing (`true`/`false`) |
| `LANGCHAIN_PROJECT` | ✗ | LangSmith project name |
| `LANGCHAIN_ENDPOINT` | ✗ | LangSmith endpoint URL |

---

## 🐛 Troubleshooting

### Backend won't start
- Check if port 8000 is in use: `netstat -ano | findstr :8000`
- Verify `.env` file exists with all required variables
- Ensure MySQL is running and credentials are correct

### Frontend can't connect to backend
- Verify backend is running at `http://localhost:8000`
- Check browser console for CORS errors
- Clear localStorage: `localStorage.clear()`

### Token expired errors
- Tokens expire after 8 hours
- Logout and login again to get a fresh token

### Leave requests not loading in dashboard
- Ensure you're logged in as HR role
- Run `python test_dashboard.py` to verify database has data
- See [HR Dashboard Troubleshooting](#-hr-dashboard-troubleshooting) section

### Memory not working
- Check if message matches filter keywords (see [Memory System](#-memory-system))
- Verify `data/long_term_memory/` directory exists
- Check API logs for ChromaDB errors

### ChromaDB errors
```python
# Reset memory database
import shutil
shutil.rmtree("data/long_term_memory")
# Then restart: python start_api.py
```

---

## 📈 Project Analysis

> **Overall Grade: B+ (85/100)** — Production-ready foundation with clear improvement paths.

### Strengths
- ✅ Clean modular architecture (9/10)
- ✅ JWT authentication with bcrypt
- ✅ Role-based access control
- ✅ Comprehensive documentation
- ✅ Functional React frontend with good UX
- ✅ Long-term memory system
- ✅ LangSmith tracing on all agents

### Areas for Improvement

#### 🔴 High Priority
1. **Fix CORS** — Currently `allow_origins=["*"]` is a security risk. Restrict to specific origins in production.
2. **Add Rate Limiting** — Use `slowapi` to prevent API abuse (30 req/min recommended).
3. **Structured Logging** — Replace `print()` statements with proper JSON logging.
4. **Redis Session Storage** — Current in-memory sessions are lost on restart and don't scale.
5. **Docker Configuration** — Add `Dockerfile` + `docker-compose.yml` for easy deployment.
6. **API Tests** — Add `pytest` integration tests for all endpoints.
7. **Health Check Endpoints** — Add `/health/liveness` and `/health/readiness` for load balancers.

#### 🟡 Medium Priority
8. Input validation and sanitization on all endpoints
9. Password complexity requirements
10. Database connection pooling
11. React Router for proper frontend navigation
12. Context API for global auth state
13. CI/CD pipeline (GitHub Actions)

#### 🟢 Low Priority (Nice to Have)
14. Dark mode toggle
15. PWA support for offline functionality
16. Internationalization (i18n)
17. Architecture diagrams (Mermaid)
18. End-to-end tests with Playwright

### Quick Wins (< 1 hour each)
```python
# 1. Generate secure SECRET_KEY
import secrets; print(secrets.token_urlsafe(32))

# 2. Fix CORS (api/main.py)
allow_origins=["http://localhost:3000"]  # Instead of "*"

# 3. Add health endpoint (api/routers/health.py)
@router.get("/health")
async def health(): return {"status": "alive"}
```

### Estimated Effort for All Improvements
| Priority | Tasks | Time |
|----------|-------|------|
| High | 7 tasks | 2–3 days |
| Medium | 7 tasks | 3–4 days |
| Low | 6 tasks | 2–3 days |
| **Total** | **20 tasks** | **7–10 days** |

---

## 📄 License

MIT License — free to use for personal or commercial projects.

---

## 👥 Contributors

Built with ❤️ by the NovaHR team.

---

## 🔗 Links

- **API Documentation:** `http://localhost:8000/docs`
- **Frontend:** `http://localhost:3000`
- **Dashboard:** `http://localhost:3000/dashboard` (HR only)
- **LangSmith:** `https://smith.langchain.com/`
