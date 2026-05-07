import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { sendMessage, clearSession } from "../services/chatService";
import { logout, getUser } from "../services/authService";
import { getOrCreateSessionId, clearSessionId } from "../utils/session";
import ChatBubble from "../components/ui/ChatBubble";

export default function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const user = getUser();
  const sessionId = getOrCreateSessionId(user?.id || "guest");

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Keep input focused on page load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Welcome message on load
  useEffect(() => {
    setMessages([
      {
        type: "bot",
        text: `Hello ${user?.name || "there"}! 👋 I'm NovaHR, your AI HR assistant. How can I help you today?`,
      },
    ]);
  }, [user?.name]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    // Add user message
    setMessages((prev) => [...prev, { type: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendMessage(text, sessionId);
      if (response) {
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: response.response },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: `⚠ Error: ${err.message}`, isError: true },
      ]);
    } finally {
      setLoading(false);
      // Refocus after state update — setTimeout ensures disabled is cleared first
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleLogout = async () => {
    await clearSession(sessionId);
    clearSessionId(user?.id || "guest");
    logout();
    navigate("/login");
  };

  const handleNewChat = async () => {
    await clearSession(sessionId);
    clearSessionId(user?.id || "guest");
    window.location.reload();
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-zinc-900 text-white flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <span className="text-2xl">💼</span>
            <span className="text-xl font-bold">NovaHR</span>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={handleNewChat}
            className="w-full bg-zinc-800 hover:bg-zinc-700 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <span className="text-lg">+</span>
            <span>New Chat</span>
          </button>
        </div>

        {/* Quick Actions */}
        <div className="flex-1 overflow-y-auto px-4 space-y-2">
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-3">Quick Actions</p>
          
          {user?.auth_role === "HR" && (
            <button
              onClick={() => navigate("/dashboard")}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-sm"
            >
              📊 HR Dashboard
            </button>
          )}
          
          <button
            onClick={() => setInput("I want to apply for leave")}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-sm"
          >
            📅 Apply for Leave
          </button>
          
          <button
            onClick={() => setInput("What is my leave balance?")}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-sm"
          >
            📊 Leave Balance
          </button>
          
          <button
            onClick={() => setInput("What is the casual leave policy?")}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-sm"
          >
            📋 Company Policy
          </button>
          
          {user?.auth_role === "HR" && (
            <button
              onClick={() => setInput("Schedule a meeting tomorrow at 3pm")}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-sm"
            >
              🗓 Schedule Meeting
            </button>
          )}
        </div>

        {/* User Info */}
        <div className="p-4 border-t border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center font-bold">
              {user?.name?.charAt(0).toUpperCase() || "U"}
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium">{user?.name || "User"}</span>
              <span className="text-xs text-gray-400">{user?.auth_role || "EMPLOYEE"}</span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white transition-colors"
            title="Logout"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900">NovaHR Assistant</h2>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-gray-600">Online</span>
            </div>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 bg-gray-50">
          {messages.map((msg, i) => (
            <ChatBubble
              key={i}
              message={msg.text}
              isBot={msg.type === "bot"}
              userInitial={user?.name?.charAt(0).toUpperCase() || "U"}
            />
          ))}

          {loading && (
            <div className="flex gap-3 mb-4 animate-fade-in">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                🤖
              </div>
              <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="flex gap-3 items-end">
            <textarea
              ref={inputRef}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              placeholder="Type your message... (Enter to send)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-blue-600 text-white p-3 rounded-xl hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              title="Send message"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </main>
    </div>
  );
}
