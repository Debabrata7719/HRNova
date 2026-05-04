# NovaHR - AI-Powered HR Assistant

> Complete HR management system with AI chatbot, leave management, email automation, calendar scheduling, and policy Q&A.

---

## 🚀 Features

### 🤖 AI Assistant
- **Multi-Agent System** — LangGraph-powered routing to specialized agents
- **Leave Management** — Apply for leave with natural language
- **Email Automation** — Compose and send emails via Gmail SMTP
- **Calendar Integration** — Schedule meetings with Google Calendar
- **Policy Q&A** — ChromaDB vector search over company policy documents
- **Leave Balance Queries** — Real-time balance checks from MySQL

### 👔 HR Dashboard
- **Leave Request Management** — View all employee leave requests
- **Approve/Reject** — One-click approval/rejection with instant updates
- **Statistics** — Real-time counts (Total, Pending, Approved, Rejected)
- **Filter & Search** — Filter by status, search by employee

### 🔐 Authentication & Security
- **JWT Token-based Auth** — Secure login with bcrypt password hashing
- **Role-based Access** — HR and Employee roles with different permissions
- **Session Management** — Stateful conversations with per-user sessions

### 🌐 REST API
- **FastAPI Backend** — Auto-generated Swagger docs at `/docs`
- **CORS Enabled** — Ready for frontend integration
- **Protected Endpoints** — JWT verification on all sensitive routes

---

## 📁 Project Structure

```
NovaHR/
├── api/                          # FastAPI backend
│   ├── dependencies/
│   │   └── auth.py              # JWT verification
│   ├── routers/
│   │   ├── auth.py              # Login endpoint
│   │   ├── chat.py              # Chat with AI agent
│   │   └── leaves.py            # Leave management (HR only)
│   ├── main.py                  # FastAPI app
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
│   │   │   ├── schedule/        # Calendar agent
│   │   │   ├── employee/        # Employee portal
│   │   │   └── general/         # General conversation
│   │   ├── memory.py            # Conversation memory
│   │   └── router.py            # LangGraph routing
│   └── tools/
│       ├── db_connection.py     # MySQL utility
│       └── embed_policy.py      # PDF embedder
│
├── novahr-frontend/             # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx        # Login page
│   │   │   ├── Chat.jsx         # AI chat interface
│   │   │   └── Dashboard.jsx   # HR dashboard
│   │   ├── services/
│   │   │   ├── authService.js   # Login/logout
│   │   │   ├── chatService.js   # Chat API
│   │   │   └── leaveService.js  # Leave API
│   │   └── utils/
│   │       └── session.js       # Session ID generation
│   └── package.json
│
├── data/
│   ├── NovaHR_Company_Policy_Notebook.pdf
│   └── chroma_db/               # Vector database
│
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
├── start_api.py                 # API server launcher
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
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Configure Environment Variables
Create `.env` file:
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

# JWT Secret
SECRET_KEY=your_super_secret_key_here

# LangSmith (optional)
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=novahr
```

#### Setup MySQL Database
```sql
CREATE DATABASE novahr;
USE novahr;

-- Create employees table
CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    department VARCHAR(100),
    password VARCHAR(255),
    auth_role VARCHAR(20)
);

-- Create leaves table
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

-- Insert sample employees
INSERT INTO employees (name, email, department, auth_role) VALUES
('Debu', 'debu@gmail.com', 'Engineering', 'HR'),
('Rahul', 'rahul@gmail.com', 'HR', 'EMPLOYEE'),
('Priya', 'priya@gmail.com', 'Marketing', 'EMPLOYEE');
```

#### Setup Authentication
```bash
python auth/setup_auth.py
```
This will hash passwords and set default credentials:
- HR: `debu@gmail.com` / `721242`
- Employees: `rahul@gmail.com` / `123`

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

## 🚀 Running the Application

### Start Backend (Terminal 1)
```bash
python start_api.py
```
API will run at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### Start Frontend (Terminal 2)
```bash
cd novahr-frontend
npm start
```
Frontend will run at `http://localhost:3000`

---

## 📖 Usage

### Web Interface

#### Login
- Go to `http://localhost:3000`
- Login with credentials:
  - **HR:** `debu@gmail.com` / `721242`
  - **Employee:** `rahul@gmail.com` / `123`

#### Chat with AI Assistant
- Ask questions: "What is my leave balance?"
- Apply for leave: "I want to apply for leave"
- Schedule meetings: "Schedule a meeting tomorrow at 3pm"
- Check policy: "What is the casual leave policy?"

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

Full API documentation: `http://localhost:8000/docs`

---

## 🧪 Testing

### Test Database Connection
```bash
python tests/test_connections.py
```

### Test API Endpoints
Use Swagger UI at `http://localhost:8000/docs`:
1. Login via `POST /api/auth/login`
2. Copy the token
3. Click **Authorize** button (🔒)
4. Paste token and click **Authorize**
5. Test any endpoint

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
LangGraph Agent Pipeline (src/main_agent/router.py)
    ↓
Specialized Agents (leave/email/query/schedule/general)
    ↓
Tools (MySQL, ChromaDB, Gmail, Google Calendar)
    ↓
Response
```

### Agent Routing
```
User Message → Router Agent
    ├─→ Leave Agent (apply for leave)
    ├─→ Email Agent (send emails)
    ├─→ Query Agent (policy Q&A, balance check)
    ├─→ Schedule Agent (calendar events)
    └─→ General Agent (conversation)
```

---

## 🔐 Security

- **Passwords:** bcrypt hashed (cost factor 12)
- **JWT Tokens:** HS256 algorithm, 8-hour expiry
- **Role-based Access:** HR vs Employee permissions enforced at API level
- **CORS:** Configured for localhost (update for production)
- **Environment Variables:** Sensitive data in `.env` (not committed)

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
- **Framework:** FastAPI
- **LLM:** Groq (Llama models)
- **Agent Framework:** LangGraph + LangChain
- **Database:** MySQL
- **Vector DB:** ChromaDB
- **Embeddings:** HuggingFace Sentence Transformers
- **Auth:** JWT (python-jose) + bcrypt

### Frontend
- **Framework:** React 18
- **Styling:** Custom CSS
- **HTTP Client:** Fetch API
- **State Management:** React Hooks

### Integrations
- **Email:** Gmail SMTP
- **Calendar:** Google Calendar API
- **Monitoring:** LangSmith (optional)

---

## 📝 Environment Variables Reference

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
| `LANGCHAIN_TRACING_V2` | ✗ | Enable LangSmith tracing |
| `LANGCHAIN_PROJECT` | ✗ | LangSmith project name |

---

## 🐛 Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify `.env` file exists and has all required variables
- Ensure MySQL is running and credentials are correct

### Frontend can't connect to backend
- Verify backend is running at `http://localhost:8000`
- Check browser console for CORS errors
- Clear localStorage and re-login: `localStorage.clear()`

### Token expired errors
- Tokens expire after 8 hours
- Logout and login again to get a fresh token

### Leave requests not loading
- Ensure backend is running (`python start_api.py`)
- Check browser console for errors
- Verify you're logged in as HR role

---

## 📄 License

MIT License - feel free to use for personal or commercial projects.

---

## 👥 Contributors

Built with ❤️ by the NovaHR team.

---

## 🔗 Links

- **API Documentation:** `http://localhost:8000/docs`
- **Frontend:** `http://localhost:3000`
- **Dashboard:** `http://localhost:3000/dashboard` (HR only)
