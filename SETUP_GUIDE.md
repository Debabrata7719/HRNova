# NovaHR Quick Setup Guide

> Get NovaHR running in 10 minutes

---

## ⚡ Quick Start

### 1. Install Dependencies (5 min)

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd novahr-frontend
npm install
cd ..
```

### 2. Configure Environment (2 min)

Copy `.env.example` to `.env` and fill in:

```env
GROQ_API_KEY=your_key_here
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=novahr
SECRET_KEY=change_this_to_random_string
```

### 3. Setup Database (2 min)

```bash
# Create database
mysql -u root -p
```

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

EXIT;
```

```bash
# Setup auth (hash passwords)
python auth/setup_auth.py

# Embed policy document
python src/tools/embed_policy.py
```

### 4. Run (1 min)

**Terminal 1 - Backend:**
```bash
python start_api.py
```

**Terminal 2 - Frontend:**
```bash
cd novahr-frontend
npm start
```

### 5. Login

Go to `http://localhost:3000`

**HR Login:**
- Email: `debu@gmail.com`
- Password: `721242`

**Employee Login:**
- Email: `rahul@gmail.com`
- Password: `123`

---

## ✅ Verify Installation

### Test Backend
```bash
# Should return: {"status":"ok","message":"NovaHR API is healthy","version":"1.0.0"}
curl http://localhost:8000/health
```

### Test Frontend
- Login page loads at `http://localhost:3000`
- After login, chat interface appears
- HR users see "📊 HR Dashboard" button

### Test Dashboard (HR only)
- Go to `http://localhost:3000/dashboard`
- Should show leave statistics and table

---

## 🔧 Common Issues

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "Cannot connect to MySQL"
- Check MySQL is running: `mysql -u root -p`
- Verify credentials in `.env`

### "Token expired" in frontend
```bash
# In browser console:
localStorage.clear()
# Then login again
```

### Backend keeps stopping
- Don't close the terminal running `python start_api.py`
- Keep it open while working

---

## 📚 Next Steps

- Read full documentation: `README.md`
- API docs: `http://localhost:8000/docs`
- Test all features in the chat interface
- Explore HR dashboard for leave management

---

## 🆘 Need Help?

Check `README.md` for detailed documentation and troubleshooting.
