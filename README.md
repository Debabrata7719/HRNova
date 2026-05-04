# NovaHR Assistant

AI-powered HR chatbot built with LangGraph, LangChain, and Groq LLM.

## Features

- **Leave Management**: Apply for leave, check balance, view status
- **Email Sending**: Send emails via Gmail SMTP
- **Policy Q&A**: Query company policies using ChromaDB vector search
- **Meeting Scheduling**: Schedule Google Calendar events
- **General Chat**: Conversational AI for HR queries

## Project Structure

```
NovaHR/
├── .env                           # Environment variables
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
│   ├── main_agent/
│   │   ├── memory.py              # ConversationBufferWindowMemory
│   │   ├── router.py              # LangGraph routing logic
│   │   │
│   │   └── agents/
│   │       ├── email/executor.py
│   │       ├── leave/executor.py
│   │       ├── scheduling/executor.py
│   │       ├── query/executor.py
│   │       ├── employee/executor.py
│   │       └── general/executor.py
│   │
│   └── tools/
│       ├── db_connection.py       # MySQL utility
│       └── embed_policy.py        # PDF embedder
│
└── tests/
    └── test_connections.py        # Connection tests
```

## Tech Stack

- **LLM**: Groq (llama-3.3-70b-versatile)
- **Framework**: LangGraph, LangChain
- **Database**: MySQL (employee/leave data)
- **Vector DB**: ChromaDB (policy embeddings)
- **Email**: Gmail SMTP
- **Calendar**: Google Calendar API
- **Tracing**: LangSmith

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
# Groq API
GROQ_API_KEY=your_groq_api_key

# Email
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password

# MySQL
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=novahr

# LangSmith (optional)
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=NovaHR
```

### 3. Setup MySQL Database

```sql
CREATE DATABASE novahr;

CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    department VARCHAR(100),
    role VARCHAR(100)
);

CREATE TABLE leaves (
    leave_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    start_date DATE,
    end_date DATE,
    leave_type VARCHAR(10),
    days INT,
    status VARCHAR(20),
    reason TEXT,
    submitted_at DATETIME,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

### 4. Embed Policy Document

```bash
python src/tools/embed_policy.py
```

This will:
- Load `data/NovaHR_Company_Policy_Notebook.pdf`
- Split into chunks
- Create embeddings using sentence-transformers
- Store in `data/chroma_db/`

### 5. Test Connections

```bash
python tests/test_connections.py
```

Should show:
```
✓ MySQL: PASS
✓ Groq API: PASS
✓ Email: PASS
✓ ChromaDB: PASS
✓ Google Calendar: PASS
```

## Usage

### Option 1: CLI Interface

#### For HR Staff (All Features)

```bash
python run_main_agent.py
```

Features:
- Leave requests
- Email sending
- Policy queries
- Meeting scheduling
- General chat

#### For Employees (Leave + Queries)

```bash
python run_employee_agent.py
```

Features:
- Apply for leave
- Check leave balance
- View leave status
- Ask policy questions

### Option 2: REST API

#### Start the API Server

```bash
uvicorn api.main:app --reload --port 8000
```

#### Access Swagger UI

Open your browser: `http://localhost:8000/docs`

#### API Features

- ✅ RESTful endpoints for chat
- ✅ Session management
- ✅ CORS enabled for frontend integration
- ✅ Auto-generated API documentation
- ✅ No authentication (development mode)

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed API usage.

## Leave Policy

- **EL (Earned Leave)**: 18 days/year
- **CL (Casual Leave)**: 12 days/year
- **SL (Sick Leave)**: 12 days/year

## Architecture

### LangGraph Router

The main agent uses LangGraph's StateGraph to route requests:

```
User Input → Router → Intent Detection → Agent Selection → Response
```

**Agents:**
- `leave_agent`: Rule-based leave workflow (no LLM)
- `email_agent`: Email composition and sending
- `query_agent`: Policy Q&A (ChromaDB) + Leave balance (MySQL)
- `schedule_agent`: Google Calendar integration
- `general_agent`: LLM-powered conversational responses

### Memory Management

Each agent has ConversationBufferWindowMemory:
- **Window size**: 5-10 messages per agent
- **Auto-summarization**: Old messages summarized before dropping
- **State persistence**: Memory serialized in LangGraph State

### Database Schema

**employees table:**
- id, name, email, department, role

**leaves table:**
- leave_id, employee_id, start_date, end_date, leave_type, days, status, reason, submitted_at

## Development

### Adding a New Agent

1. Create `src/main_agent/agents/new_agent/executor.py`
2. Implement agent function with State parameter
3. Add to `src/main_agent/router.py`:
   - Import agent
   - Add node to graph
   - Add routing logic
   - Add edge to END

### Running Tests

```bash
# Test all connections
python tests/test_connections.py

# Test specific agent (example)
python -c "from src.main_agent.agents.leave.executor import leave_agent; print('Leave agent loaded')"
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, ensure you're running from project root:

```bash
cd /path/to/NovaHR
python run_main_agent.py
```

### ChromaDB Not Found

Run the embedder:

```bash
python src/tools/embed_policy.py
```

### MySQL Connection Failed

Check `.env` credentials and ensure MySQL is running:

```bash
mysql -u root -p
```

### Google Calendar Auth

If `token.json` is invalid, delete it and re-authenticate:

```bash
rm token.json
# Run schedule agent and follow OAuth flow
```

## License

MIT

## Contributors

- Debabrata Dey (debabratadey8080@gmail.com)

## Session History

See `AGENTS.md` for detailed session history and implementation notes.
