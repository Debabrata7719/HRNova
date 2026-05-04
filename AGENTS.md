# NovaHR Agent Memory

> Read this file at session start to understand project context and history

## Project Overview
- **Project Name:** NovaHR Assistant
- **Type:** HR Chatbot with LangGraph/LangChain
- **Purpose:** Handle leave requests, email sending, and general HR queries
- **Tech Stack:** Python, Groq LLM, MySQL, LangGraph

## Current Status

### Completed Features
1. **Main Router Agent** - LangGraph StateGraph routing based on intent (leave/email/general)
2. **Leave Agent** - Rule-based workflow: identify → leave type → dates → reason → confirm → submit
3. **Email Agent** - Email composition and sending via Gmail SMTP
4. **General Agent** - LLM-powered conversational responses
5. **Memory System** - ConversationBufferWindowMemory with auto-summarization (per-agent)
6. **Database** - MySQL connection for employee/leave data
7. **Policy Vector DB** - ChromaDB with company policy PDF embedded (29 chunks)
8. **Query Agent** - Policy Q&A + leave balance from MySQL
9. **Employee Agent** - Combined interface for employees (leave + queries)

### Pending Features (from plan.md)
1. [x] **Schedule Agent** - Google Calendar integration
2. [x] **Leave Status Check** - Allow users to query leave request status

## Project Structure
```
NovaHR/
├── .env
├── .gitignore
├── requirements.txt
├── run_main_agent.py              # Main HR agent (router)
├── run_employee_agent.py          # Employee portal
├── Credentials.json               # Google OAuth credentials
├── token.json                     # Google OAuth token
│
├── data/
│   ├── NovaHR_Company_Policy_Notebook.pdf
│   └── chroma_db/                 # Vector database
│
├── src/
│   ├── __init__.py
│   │
│   ├── main_agent/
│   │   ├── __init__.py
│   │   ├── memory.py              # ConversationBufferWindowMemory
│   │   ├── router.py              # LangGraph routing logic
│   │   │
│   │   └── agents/
│   │       ├── __init__.py
│   │       ├── email/
│   │       │   ├── __init__.py
│   │       │   └── executor.py    # Email agent
│   │       ├── leave/
│   │       │   ├── __init__.py
│   │       │   └── executor.py    # Leave agent
│   │       ├── scheduling/
│   │       │   ├── __init__.py
│   │       │   └── executor.py    # Schedule agent
│   │       ├── query/
│   │       │   ├── __init__.py
│   │       │   └── executor.py    # Query agent
│   │       ├── employee/
│   │       │   ├── __init__.py
│   │       │   └── executor.py    # Employee agent
│   │       └── general/
│   │           ├── __init__.py
│   │           └── executor.py    # General agent
│   │
│   └── tools/
│       ├── __init__.py
│       ├── db_connection.py       # MySQL utility
│       └── embed_policy.py        # PDF embedder
│
└── tests/
    ├── __init__.py
    └── test_connections.py        # Connection tests
```

## Database Schema
- **employees** table: id, name, email, department, ...
- **leaves** table: id, employee_id, start_date, end_date, leave_type, days, status, reason, submitted_at

## Leave Policy
- EL (Earned Leave): 18 days/year
- CL (Casual Leave): 12 days/year
- SL (Sick Leave): 12 days/year

## Key Implementation Details
- Memory serialized in State dict (not persistent across sessions)
- Leave agent is rule-based (no LLM) to avoid rate limits
- Email uses Gmail SMTP with app password
- State flows: initial → identify → ask_* → confirm_request → completed
- Query agent uses ChromaDB for policy Q&A + MySQL for leave balance

## Run Commands
| Command | Usage |
|---------|-------|
| `python run_main_agent.py` | HR uses (all agents via router) |
| `python run_employee_agent.py` | Employees use (leave + query) |
| `python src/tools/embed_policy.py` | Embed PDF to ChromaDB |
| `python tests/test_connections.py` | Test all connections |

## Last Session Notes
> Read at session start

---

## Session History

### 2026-05-04 (continued)
**What happened:**
- Fixed schedule_agent credentials issue (OAuth token expired)
- Created authentication scripts to refresh token
- Added debug logs to verify event creation
- Fixed main_agent State to pass schedule_* fields correctly
- Added LangSmith @traceable to all agents

**User requested:**
- Debug why events weren't appearing in calendar
- Fix date/time parsing (2026 year issue, 4pm parsing)
- Clean up OAuth authentication flow

**What was done:**
- Created auth_final.py to complete OAuth flow
- Added schedule_title, schedule_date, schedule_time, schedule_description to State
- Updated LLM prompt to correctly parse dates (2026 year)
- Fixed schedule_agent to use schedule_* field names for main_agent compatibility
- Added @traceable to leave_agent, email_agent, general_agent, query_agent, schedule_agent
- Verified events ARE created (API returns event with htmlLink)
- Cleaned up debug logs after verification

**Important finding:**
- Events ARE being created - they appear in Google Calendar
- The issue was timezone confusion (4pm IST = 10:30 UTC)
- Now shows "(Asia/Kolkata IST)" in responses

**Outstanding issues:**
- None - schedule agent working correctly

---

### 2026-05-04
**What happened:**
- Added leave status check feature to query_agent
- Created schedule_agent for Google Calendar integration

**User requested:**
- Leave status check: check if leave request approved/pending/rejected
- Schedule agent: schedule meetings via natural language

**What was done:**
- Added get_leave_status() and format_status_response() to query_agent.py
- Added status detection keywords: "status", "approved", "pending", "rejected", "my leave", "leave request"
- Created schedule_agent.py with agentic workflow using LLM for date parsing
- Updated main_agent.py to route "schedule/meeting/calendar" to schedule_agent
- Fixed employee_agent.py routing (removed "leave" from query keywords to avoid misrouting)

**Outstanding issues:**
- None - both features implemented and tested

---

### 2026-05-03
**What happened:**
- Connected employee_agent with main_agent
- Added query_agent routing in LangGraph

**User requested:**
- Connect employee_agent with main_agent so HR can also use query features
- Main agent should route balance/policy queries to query_agent

**What was done:**
- Updated main_agent.py to include query_agent node
- Added "query_request" intent for balance/policy queries
- Query agent now: Policy Q&A (ChromaDB) + Leave Balance (MySQL)
- Tested "what is my leave balance" → returns EL/CL/SL
- Tested "what is casual leave policy" → returns policy from ChromaDB
- Added chroma_db/ to .gitignore

**Outstanding issues:**
- None - integration working

---

*Update this file after each session to maintain context across reconnections*