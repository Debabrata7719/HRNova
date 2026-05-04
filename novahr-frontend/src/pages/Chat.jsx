import { useState, useEffect, useRef } from "react";
import { sendMessage, clearSession } from "../services/chatService";
import { logout, getUser } from "../services/authService";
import { getOrCreateSessionId, clearSessionId } from "../utils/session";
import "./Chat.css";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const user = getUser();
  const sessionId = getOrCreateSessionId(user?.id || "guest");

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
  };

  const handleNewChat = async () => {
    await clearSession(sessionId);
    clearSessionId(user?.id || "guest");
    window.location.reload();
  };

  return (
    <div className="chat-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">💼</span>
          <span className="sidebar-title">NovaHR</span>
        </div>

        <button className="new-chat-btn" onClick={handleNewChat}>
          + New Chat
        </button>

        <div className="sidebar-section">
          <p className="sidebar-label">Quick Actions</p>
          {user?.auth_role === "HR" && (
            <button
              className="quick-btn"
              onClick={() => (window.location.href = "/dashboard")}
            >
              📊 HR Dashboard
            </button>
          )}
          <button
            className="quick-btn"
            onClick={() => setInput("I want to apply for leave")}
          >
            📅 Apply for Leave
          </button>
          <button
            className="quick-btn"
            onClick={() => setInput("What is my leave balance?")}
          >
            📊 Leave Balance
          </button>
          <button
            className="quick-btn"
            onClick={() => setInput("What is the casual leave policy?")}
          >
            📋 Company Policy
          </button>
          <button
            className="quick-btn"
            onClick={() => setInput("Schedule a meeting tomorrow at 3pm")}
          >
            🗓 Schedule Meeting
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.name?.charAt(0).toUpperCase() || "U"}
            </div>
            <div className="user-details">
              <span className="user-name">{user?.name || "User"}</span>
              <span className="user-role">{user?.auth_role || "EMPLOYEE"}</span>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Logout">
            ⎋
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-main">
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-info">
            <h2>NovaHR Assistant</h2>
            <span className="status-dot" /> Online
          </div>
        </header>

        {/* Messages */}
        <div className="messages-area">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`message-row ${msg.type === "user" ? "user-row" : "bot-row"}`}
            >
              {msg.type === "bot" && (
                <div className="avatar bot-avatar">🤖</div>
              )}
              <div
                className={`message-bubble ${
                  msg.type === "user" ? "user-bubble" : "bot-bubble"
                } ${msg.isError ? "error-bubble" : ""}`}
              >
                {msg.text.split("\n").map((line, j) => (
                  <span key={j}>
                    {line}
                    {j < msg.text.split("\n").length - 1 && <br />}
                  </span>
                ))}
              </div>
              {msg.type === "user" && (
                <div className="avatar user-avatar-icon">
                  {user?.name?.charAt(0).toUpperCase() || "U"}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message-row bot-row">
              <div className="avatar bot-avatar">🤖</div>
              <div className="message-bubble bot-bubble typing-bubble">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              className="chat-input"
              placeholder="Type your message... (Enter to send)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              title="Send message"
            >
              ➤
            </button>
          </div>
          <p className="input-hint">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </main>
    </div>
  );
}
