# NovaHR Frontend

A modern, responsive React-based HR management system frontend with AI-powered chatbot assistance, leave management, and administrative dashboards.

## Overview

NovaHR Frontend is a Single Page Application (SPA) built with React 19 that provides:

- **AI-Powered Chat Assistant** - Employees can ask HR-related questions and receive instant answers powered by LLM
- **Leave Management System** - Apply, track, and manage leave requests with approval workflows
- **HR Dashboard** - Comprehensive analytics and employee management for HR personnel
- **Role-Based Access Control** - Separate interfaces for employees and HR staff
- **Employee Management** - Add, update, and manage employee records (HR only)
- **Memory Management** - AI system learns from interactions to provide better assistance

## Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| **Frontend Framework** | React | 19.2.5 |
| **Routing** | React Router | 7.14.2 |
| **Styling** | Tailwind CSS | 3.4.1 |
| **Animations** | Framer Motion | 12.38.0 |
| **HTTP Client** | Axios | 1.7.9 |
| **UI Components** | Custom + Recharts | Latest |
| **Node.js** | Node.js | 18+ |
| **Package Manager** | npm | 8+ |

## Quick Start

### Prerequisites

- Node.js 18.x or higher
- npm 8.x or higher
- Backend API running on `http://localhost:8000` (or configured in `.env`)

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd novahr-frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create environment configuration file:**
   ```bash
   cp .env.example .env
   ```
   Or create `.env` with:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Start the development server:**
   ```bash
   npm start
   ```

   The app will open at `http://localhost:3000` and automatically reload when you make changes.

## Available Scripts

### Development

- **`npm start`** - Runs app in development mode with hot reload
  - Opens `http://localhost:3000` automatically
  - Shows lint errors in console

- **`npm test`** - Launches test runner in interactive watch mode
  - Press `a` to run all tests
  - Press `o` to run only changed files

### Production

- **`npm run build`** - Builds app for production to the `build/` folder
  - Minifies and optimizes all assets
  - Includes file hashing for caching
  - Ready for deployment

- **`npm run eject`** - One-way operation to expose all configuration
  - Not typically needed
  - Gives full control over webpack, Babel, ESLint configs
  - **Note:** This is irreversible

## Project Structure

```
novahr-frontend/
├── public/
│   ├── index.html          # Main HTML entry point
│   ├── favicon.ico
│   └── manifest.json       # PWA configuration
├── src/
│   ├── components/
│   │   └── ui/
│   │       ├── Button.jsx      # Reusable button component
│   │       ├── Card.jsx        # Card wrapper component
│   │       ├── ChatBubble.jsx  # Chat message display
│   │       ├── Input.jsx       # Form input wrapper
│   │       └── Spinner.jsx     # Loading indicator
│   ├── pages/
│   │   ├── Landing.jsx         # Home/landing page
│   │   ├── Login.jsx           # Authentication page
│   │   ├── Chat.jsx            # Chat interface with AI bot
│   │   ├── Dashboard.jsx       # HR analytics dashboard
│   │   └── NotFound.jsx        # 404 page
│   ├── services/
│   │   ├── api.js          # Axios instance with base config
│   │   ├── authService.js  # Login/logout/token management
│   │   ├── chatService.js  # Chat API calls
│   │   ├── leaveService.js # Leave request APIs
│   │   ├── employeeService.js # Employee management APIs
│   │   └── memoryService.js   # Memory management APIs
│   ├── config/
│   │   └── api.js          # Centralized API configuration
│   ├── utils/
│   │   └── sessionUtils.js # Session and token helpers
│   ├── assets/
│   │   └── [images]        # Images and static assets
│   ├── App.jsx             # Root component with routing
│   ├── App.css             # Global styles
│   └── index.js            # React entry point
├── package.json            # Dependencies and scripts
├── package-lock.json       # Locked dependency versions
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file

```

## Pages & Routes

### Public Routes

- **`/`** - Landing Page
  - Introduction to NovaHR
  - Call-to-action for login
  - Feature highlights

- **`/login`** - Login Page
  - Email and password authentication
  - Error handling and validation
  - Redirect to Dashboard or Chat after login

### Protected Routes (Requires Authentication)

- **`/chat`** - Chat Interface
  - Real-time chat with AI assistant
  - Message history in session
  - Typing indicators and loading states
  - Features: policy Q&A, leave info, general HR queries

- **`/dashboard`** - HR Analytics Dashboard (HR Role Only)
  - Employee statistics and charts
  - Leave approval requests
  - Department-wise analytics
  - Leave balance overview
  - Employee management forms

- **`/404`** - Not Found Page
  - Displayed for invalid routes

## Core Features

### 1. Authentication System

**Login Flow:**
- Email and password credentials
- JWT token-based authentication
- Token stored in localStorage with 8-hour expiry
- Automatic redirect on auth failure
- Session persistence across page reloads

**Service:** `src/services/authService.js`
- `login(email, password)` - Authenticate user
- `logout()` - Clear session
- `getToken()` - Retrieve stored JWT
- `isAuthenticated()` - Check auth status

### 2. AI Chat Assistant

**Features:**
- Real-time conversation with AI
- Message persistence within session
- Policy question answering
- Leave balance queries
- General HR assistance
- Context awareness from memory system

**Service:** `src/services/chatService.js`
- `sendMessage(sessionId, message)` - Send chat message
- `getSessionHistory(sessionId)` - Fetch message history

**Page:** `src/pages/Chat.jsx`
- Message input with validation
- Auto-scrolling message display
- Typing indicators
- Error handling

### 3. Leave Management

**Features:**
- View current leave balance
- Apply for new leave requests
- Track leave status (pending/approved/rejected)
- HR approval workflow
- Leave type categories (EL, CL, SL)

**Service:** `src/services/leaveService.js`
- `applyLeave(leaveData)` - Submit leave request
- `getLeaveBalance(employeeId)` - Check balance
- `getLeaveHistory(employeeId)` - View past requests
- `approveLeave(leaveId)` - Approve request (HR)
- `rejectLeave(leaveId)` - Reject request (HR)

### 4. Employee Management (HR Only)

**Features:**
- Add new employees
- Bulk upload employee CSV
- Update employee details
- View employee list with filters

**Service:** `src/services/employeeService.js`
- `addEmployee(employeeData)` - Create new employee
- `getEmployees()` - List all employees
- `updateEmployee(employeeId, data)` - Update employee
- `bulkImportEmployees(csvFile)` - Batch upload

### 5. Memory Management

**Features:**
- Clear conversation memories
- Export memory data
- Memory quality feedback

**Service:** `src/services/memoryService.js`
- `clearMemory()` - Delete all memories
- `getMemoryStats()` - View memory statistics
- `exportMemory()` - Download memory data

## Configuration

### Environment Variables

Create a `.env` file in the `novahr-frontend/` directory:

```
# Backend API Configuration
REACT_APP_API_URL=http://localhost:8000

# Optional: For production deployment
# REACT_APP_API_URL=https://api.example.com

# Optional: Application environment
REACT_APP_ENV=development
```

**Available Variables:**
- `REACT_APP_API_URL` - Backend API base URL (default: `http://localhost:8000`)
- `REACT_APP_ENV` - Environment (development/production)

### API Configuration

File: `src/config/api.js`

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
  },
  CHAT: {
    SEND: '/api/chat/send',
    HISTORY: '/api/chat/history',
  },
  // ... more endpoints
};
```

## API Integration

### Axios Instance

File: `src/services/api.js`

All API calls use a centralized Axios instance with:
- Base URL from environment configuration
- JWT token in Authorization header
- Error handling middleware
- Request/response interceptors

Example:
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
});

// Token is automatically added to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Backend API Endpoints

**Authentication:**
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

**Chat:**
- `POST /api/chat/send` - Send message to AI
- `GET /api/chat/history/{sessionId}` - Get chat history

**Leaves:**
- `GET /api/leaves/balance` - Get leave balance
- `POST /api/leaves/apply` - Apply for leave
- `GET /api/leaves/my-leaves` - Get employee's leaves
- `PUT /api/leaves/{id}/approve` - Approve leave (HR)
- `PUT /api/leaves/{id}/reject` - Reject leave (HR)

**Employees:**
- `GET /api/employees` - List all employees
- `POST /api/employees` - Add new employee
- `PUT /api/employees/{id}` - Update employee
- `POST /api/employees/bulk` - Bulk import

**Memory:**
- `DELETE /api/chat/memory` - Clear memory
- `GET /api/chat/memory/stats` - Memory statistics

## Development Guidelines

### Adding a New Page

1. **Create page component:**
   ```bash
   touch src/pages/MyPage.jsx
   ```

2. **Import in App.jsx and add route:**
   ```javascript
   import MyPage from './pages/MyPage';
   
   <Route path="/mypage" element={<MyPage />} />
   ```

3. **Use authentication wrapper:**
   ```javascript
   import { useEffect, useState } from 'react';
   import authService from '../services/authService';

   function MyPage() {
     useEffect(() => {
       if (!authService.isAuthenticated()) {
         navigate('/login');
       }
     }, []);
     
     return <div>My Page Content</div>;
   }
   ```

### Adding a New Service

1. **Create service file:**
   ```bash
   touch src/services/myService.js
   ```

2. **Import and use Axios:**
   ```javascript
   import api from './api';

   export const myFunction = async (data) => {
     const response = await api.post('/api/endpoint', data);
     return response.data;
   };
   ```

3. **Use in components:**
   ```javascript
   import { myFunction } from '../services/myService';

   // In component
   const result = await myFunction(data);
   ```

### Adding a New Component

1. **Create component file:**
   ```bash
   touch src/components/MyComponent.jsx
   ```

2. **Export as default:**
   ```javascript
   function MyComponent({ prop1, prop2 }) {
     return <div>{prop1} {prop2}</div>;
   }

   export default MyComponent;
   ```

3. **Use in pages:**
   ```javascript
   import MyComponent from '../components/MyComponent';
   ```

### Styling with Tailwind CSS

All components use Tailwind CSS for styling:

```javascript
function Button({ children, onClick, variant = 'primary' }) {
  const baseStyles = 'px-4 py-2 rounded font-medium transition';
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

### Using Framer Motion for Animations

```javascript
import { motion } from 'framer-motion';

function AnimatedComponent() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.3 }}
    >
      Content
    </motion.div>
  );
}
```

## State Management

Currently, the application uses:
- **React Hooks** (useState, useContext, useReducer) for local state
- **localStorage** for persistent data (tokens, user info)
- **Component Props** for passing data between components

### Recommended Patterns

**For global state (user info, auth status):**
```javascript
// Create context
const AuthContext = React.createContext();

// Provider component
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  return <AuthContext.Provider value={{ user, setUser }}>{children}</AuthContext.Provider>;
}

// Use in component
const { user, setUser } = useContext(AuthContext);
```

**For API data:**
```javascript
const [data, setData] = useState(null);
const [loading, setLoading] = useState(false);

useEffect(() => {
  setLoading(true);
  fetchData().then(setData).finally(() => setLoading(false));
}, []);
```

## Error Handling

### API Errors

All API calls should handle errors gracefully:

```javascript
try {
  const result = await leaveService.applyLeave(leaveData);
  console.log('Success:', result);
} catch (error) {
  console.error('Error applying leave:', error.response?.data?.error || error.message);
  setError('Failed to apply leave. Please try again.');
}
```

### Common Error Scenarios

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Redirect to login |
| 403 Forbidden | Insufficient permissions | Show permission error |
| 400 Bad Request | Invalid data sent | Validate form inputs |
| 500 Server Error | Backend issue | Show generic error message |
| Network Error | API unreachable | Check API URL in .env |

## Authentication Flow

```
┌─────────────────────────────────────────────────────┐
│                    User Actions                     │
└────────┬────────────────────────────────────────────┘
         │
         ▼
    /login page
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
    Login Success            Login Failed
         │                         │
         ├─ Generate JWT ◄────────┘
         │
         ├─ Store in localStorage
         │
         ├─ Redirect to /chat or /dashboard
         │
         ▼
    Protected Pages
         │
         ├─ Token added to all API requests
         │
         ├─ Token expires in 8 hours
         │
         ├─ User logs out (manual)
         │
         ▼
    /login page again
```

## Troubleshooting

### 1. "Cannot find module" errors

**Solution:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### 2. Blank page on startup

**Check:**
- Is the backend API running on `http://localhost:8000`?
- Is `.env` configured with correct `REACT_APP_API_URL`?
- Open browser console (F12) for error messages

**Solution:**
```bash
npm start
# Check console for specific error
```

### 3. "Network Error" or "Cannot connect to server"

**Solution:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Update .env API URL if needed
REACT_APP_API_URL=http://YOUR_API_URL:8000
```

### 4. Token/Session errors after login

**Solution:**
```bash
# Clear localStorage in browser console
localStorage.clear()
# Refresh page and login again
```

### 5. CSS not applying (Tailwind styles missing)

**Verify:**
- Run `npm install` to ensure Tailwind is installed
- Check `tailwind.config.js` includes all template paths
- Restart dev server after installing

### 6. Hot reload not working

**Solution:**
```bash
# Stop the server (Ctrl+C)
# Clear cache and restart
npm start
```

## Performance Optimization

### Built-in Optimizations

1. **Code Splitting** - Lazy load pages with React.lazy() for faster initial load
2. **Image Optimization** - Serve optimized images, consider WebP format
3. **Minification** - Production build automatically minifies all code
4. **Caching** - Tailwind CSS purges unused styles in production

### Recommended Improvements (Future)

1. Implement React.memo for expensive components
2. Use useCallback/useMemo for performance-critical logic
3. Add service worker for offline support
4. Implement virtual scrolling for large lists
5. Deploy to CDN for static assets

## Deployment

### Build for Production

```bash
npm run build
```

Creates optimized build in `build/` folder:
- Minified JavaScript and CSS
- Asset hashing for caching
- Removed source maps
- Optimized bundle size

### Deployment Options

**Option 1: Vercel (Recommended)**
```bash
npm install -g vercel
vercel
```

**Option 2: Netlify**
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=build
```

**Option 3: Traditional Server**
```bash
# Copy build folder to server
scp -r build/ user@server:/var/www/novahr/

# Serve with Nginx or Apache
# Set REACT_APP_API_URL to production API URL before building
```

**Option 4: Docker**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables for Production

Before deploying, update `.env` with production values:

```
REACT_APP_API_URL=https://api.example.com
REACT_APP_ENV=production
```

Then rebuild:
```bash
npm run build
```

## Security Considerations

### ✅ Implemented

- JWT-based authentication with 8-hour expiry
- Tokens stored in secure storage
- HTTPS required for production
- Input validation on forms
- CORS configured on backend

### 🔒 Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Keep dependencies updated** - Run `npm audit` regularly
3. **Validate user input** - Check data before sending to API
4. **Use HTTPS** - Always encrypt data in transit
5. **Rotate secrets** - Change API keys periodically
6. **Monitor access logs** - Track unusual activity

### Recommended Additions

- Add Content Security Policy (CSP) headers
- Implement rate limiting on frontend
- Add request signing for sensitive operations
- Regular security audits and penetration testing

## Support & Resources

### Documentation
- **Main Project README:** See `../../README.md` for full system documentation
- **API Documentation:** See `../../API.md` for backend endpoints
- **Scalability Guide:** See `../../SCALABILITY.md` for future improvements

### External Resources
- [React Documentation](https://react.dev)
- [React Router Guide](https://reactrouter.com)
- [Tailwind CSS Docs](https://tailwindcss.com)
- [Framer Motion](https://www.framer.com/motion/)
- [Axios Documentation](https://axios-http.com)

### Getting Help

1. Check the **Troubleshooting** section above
2. Review **Error Handling** guidelines
3. Check browser console (F12) for error messages
4. Review `src/services/api.js` for API configuration
5. Verify backend API is running and accessible

## Contributing

### Before Committing

1. Run tests: `npm test`
2. Check for lint errors
3. Test all modified features locally
4. Update documentation if adding new features
5. Verify `.env` is not committed

### Code Style

- Use functional components with hooks
- Use meaningful variable and function names
- Add comments for complex logic
- Keep components focused and reusable
- Use Tailwind CSS for styling (not inline styles)

## License

This project is part of the NovaHR system. See main project LICENSE file.

---

**Last Updated:** May 14, 2026
**Version:** 1.0.0
**Maintained by:** NovaHR Development Team
