# NovaHR Frontend - Source Structure

## Folder Organization

```
src/
├── assets/          # Static assets (images, icons, fonts)
├── components/      # Reusable React components
│   └── ui/          # UI primitives (Button, Card, Input, etc.)
├── config/          # Configuration files
│   └── api.js       # API base URL and endpoints
├── hooks/           # Custom React hooks
├── pages/           # Page components (one per route)
├── services/        # API service layer (auth, chat, leaves)
├── utils/           # Utility functions (session management, helpers)
├── App.jsx          # Main app component with routing
├── index.css        # Global styles (Tailwind directives)
└── index.js         # React entry point
```

## Key Files

### Configuration
- **`config/api.js`** - Centralized API base URL. Change once, applies to all services.

### Pages
- **`pages/Landing.jsx`** - Public landing page with animations
- **`pages/Login.jsx`** - Authentication page
- **`pages/Chat.jsx`** - Main AI assistant chat interface
- **`pages/Dashboard.jsx`** - HR leave management dashboard
- **`pages/NotFound.jsx`** - 404 error page

### Services (API Layer)
- **`services/authService.js`** - Login, logout, token management
- **`services/chatService.js`** - Send messages, clear sessions
- **`services/leaveService.js`** - Leave CRUD operations (HR only)

### Components
- **`components/ui/Button.jsx`** - Reusable button with variants
- **`components/ui/Card.jsx`** - Card container with hover effects
- **`components/ui/ChatBubble.jsx`** - Message bubble for chat interface
- **`components/ui/Input.jsx`** - Form input with label and error states
- **`components/ui/LoadingSpinner.jsx`** - Loading indicator

### Utils
- **`utils/session.js`** - Session ID generation and localStorage management

## Naming Conventions

- **Components**: PascalCase (e.g., `ChatBubble.jsx`)
- **Services**: camelCase (e.g., `authService.js`)
- **Utils**: camelCase (e.g., `session.js`)
- **Config**: camelCase (e.g., `api.js`)

## Import Paths

All imports use relative paths from the current file:

```javascript
// From a page
import API_BASE from "../config/api";
import { login } from "../services/authService";
import Button from "../components/ui/Button";

// From a service
import API_BASE from "../config/api";

// From a component
import clsx from "clsx";  // External packages use direct imports
```

## Adding New Features

### New Page
1. Create `pages/NewPage.jsx`
2. Add route in `App.jsx`
3. Add navigation link in sidebar (if needed)

### New Service
1. Create `services/newService.js`
2. Import `API_BASE` from `config/api.js`
3. Export functions that call the API

### New Component
1. Create `components/ui/NewComponent.jsx` (if UI primitive)
2. Or create `components/NewComponent.jsx` (if feature-specific)
3. Export as default

### New Hook
1. Create `hooks/useNewHook.js`
2. Export the hook function
3. Import and use in components

## Code Style

- **Tailwind CSS** for all styling (no CSS files)
- **Functional components** with hooks
- **React Router** for navigation
- **Framer Motion** for animations
- **Recharts** for data visualization

## Environment

- **Development**: `npm start` (runs on `http://localhost:3000`)
- **Build**: `npm run build`
- **Test**: `npm test`
