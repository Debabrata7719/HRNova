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
1. [ ] **Schedule Agent** - Google Calendar integration
2. [ ] **Leave Status Check** - Allow users to query leave request status

## Project Structure
```
NOVA/
├── main_agent.py       # Router with LangGraph
├── leave_agent.py      # Leave request workflow
├── email_chatbot.py   # Email sending
├── general_agent.py   # General chat
├── query_agent.py      # Policy Q&A + Leave balance
├── employee_agent.py   # Employee portal (leave + query)
├── embed_policy.py     # PDF embedder for ChromaDB
├── memory_manager.py  # ConversationBufferWindowMemory
├── db_connection.py  # MySQL utility
├── chroma_db/        # Vector database (policy embeddings)
├── requirements.txt  # Dependencies
├── plan.md           # Feature roadmap
├── .env             # Secrets
└── Credentials.json  # Service credentials
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
| `python main_agent.py` | HR uses (all agents via router) |
| `python employee_agent.py` | Employees use (leave + query) |
| `python leave_agent.py --standalone` | Employees use (leave only) |
| `python embed_policy.py` | Embed PDF to ChromaDB |

## Last Session Notes
> Read at session start

---

## Session History

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