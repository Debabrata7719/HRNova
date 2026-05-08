import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  SendIcon, LoaderIcon, Paperclip, Command,
  CalendarDays, BarChart2, BookOpen, CalendarClock,
  LayoutDashboard, ChevronLeft, ChevronRight, LogOut, Search,
} from "lucide-react";
import botAvatar from "../assets/bot-avatar.png";
import { sendMessage, clearSession } from "../services/chatService";
import { logout, getUser } from "../services/authService";
import { getLeaveStats } from "../services/leaveService";
import { getOrCreateSessionId, clearSessionId } from "../utils/session";
import ChatBubble from "../components/ui/ChatBubble";

const LOGO = process.env.PUBLIC_URL + "/bot-avatar.png";

function cn(...classes) { return classes.filter(Boolean).join(" "); }

// ── Auto-resize textarea ──────────────────────────────────────────────────────
function useAutoResizeTextarea({ minHeight, maxHeight }) {
  const textareaRef = useRef(null);
  const adjustHeight = useCallback((reset) => {
    const t = textareaRef.current;
    if (!t) return;
    if (reset) { t.style.height = `${minHeight}px`; return; }
    t.style.height = `${minHeight}px`;
    t.style.height = `${Math.max(minHeight, Math.min(t.scrollHeight, maxHeight ?? Infinity))}px`;
  }, [minHeight, maxHeight]);
  useEffect(() => { if (textareaRef.current) textareaRef.current.style.height = `${minHeight}px`; }, [minHeight]);
  useEffect(() => {
    const h = () => adjustHeight();
    window.addEventListener("resize", h);
    return () => window.removeEventListener("resize", h);
  }, [adjustHeight]);
  return { textareaRef, adjustHeight };
}

// ── Textarea with violet focus ring ──────────────────────────────────────────
const Textarea = ({ className, containerClassName, showRing = true, ...props }) => {
  const [isFocused, setIsFocused] = useState(false);
  return (
    <div className={cn("relative", containerClassName)}>
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
          "transition-all duration-200 ease-in-out placeholder:text-muted-foreground",
          "disabled:cursor-not-allowed disabled:opacity-50",
          showRing ? "focus-visible:outline-none focus-visible:ring-0 focus-visible:ring-offset-0" : "",
          className
        )}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        {...props}
      />
      {showRing && isFocused && (
        <motion.span
          className="absolute inset-0 rounded-md pointer-events-none ring-2 ring-offset-0 ring-violet-500/30"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        />
      )}
    </div>
  );
};

// ── Typing dots ───────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex items-center ml-1">
      {[1, 2, 3].map((dot) => (
        <motion.div key={dot} className="w-1.5 h-1.5 bg-white/90 rounded-full mx-0.5"
          initial={{ opacity: 0.3 }}
          animate={{ opacity: [0.3, 0.9, 0.3], scale: [0.85, 1.1, 0.85] }}
          transition={{ duration: 1.2, repeat: Infinity, delay: dot * 0.15, ease: "easeInOut" }}
          style={{ boxShadow: "0 0 4px rgba(255,255,255,0.3)" }}
        />
      ))}
    </div>
  );
}

// ── Main Chat ─────────────────────────────────────────────────────────────────
export default function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [activeCmd, setActiveCmd] = useState(-1);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [pendingLeaves, setPendingLeaves] = useState(null);
  const messagesEndRef = useRef(null);
  const commandPaletteRef = useRef(null);

  const { textareaRef, adjustHeight } = useAutoResizeTextarea({ minHeight: 60, maxHeight: 200 });
  const user = getUser();
  const sessionId = getOrCreateSessionId(user?.id || "guest");
  const isHR = user?.auth_role === "HR";

  // Fetch pending leave count for HR badge
  useEffect(() => {
    if (!isHR) return;
    getLeaveStats()
      .then((s) => setPendingLeaves(s.pending ?? 0))
      .catch(() => setPendingLeaves(null));
  }, []); // eslint-disable-line

  // Commands — HR Dashboard removed (now in sidebar)
  const allCommands = [
    {
      icon: <CalendarDays className="w-4 h-4" />,
      label: "Apply for Leave",
      description: "Submit a new leave request (Earned, Casual or Sick leave)",
      message: "I want to apply for leave",
      roles: ["HR", "EMPLOYEE"],
    },
    {
      icon: <BarChart2 className="w-4 h-4" />,
      label: "Check Leave Balance",
      description: "View your remaining EL, CL and SL days for this year",
      message: "What is my leave balance?",
      roles: ["HR", "EMPLOYEE"],
    },
    {
      icon: <BookOpen className="w-4 h-4" />,
      label: "Company Policy",
      description: "Ask about leave rules, notice period or code of conduct",
      message: "What is the casual leave policy?",
      roles: ["HR", "EMPLOYEE"],
    },
    {
      icon: <CalendarClock className="w-4 h-4" />,
      label: "Schedule a Meeting",
      description: "Book a Google Calendar event for a specific date and time",
      message: "Schedule a meeting tomorrow at 3pm",
      roles: ["HR"],
    },
  ];
  const commands = allCommands.filter((c) => c.roles.includes(user?.auth_role || "EMPLOYEE"));

  // Close palette on outside click
  useEffect(() => {
    const handler = (e) => {
      const btn = document.querySelector("[data-command-button]");
      if (commandPaletteRef.current && !commandPaletteRef.current.contains(e.target) && !btn?.contains(e.target))
        setShowCommandPalette(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    const h = (e) => setMousePosition({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", h);
    return () => window.removeEventListener("mousemove", h);
  }, []);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  useEffect(() => { textareaRef.current?.focus(); }, []); // eslint-disable-line
  useEffect(() => {
    setMessages([{ type: "bot", text: `Hello ${user?.name || "there"}! 👋 I'm NovaHR, your AI HR assistant. How can I help you today?` }]);
  }, [user?.name]);

  const selectCommand = (cmd) => {
    setShowCommandPalette(false); setActiveCmd(-1);
    setInput(cmd.message);
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setMessages((p) => [...p, { type: "user", text }]);
    setInput(""); adjustHeight(true); setLoading(true);
    try {
      const res = await sendMessage(text, sessionId);
      if (res) setMessages((p) => [...p, { type: "bot", text: res.response }]);
    } catch (err) {
      setMessages((p) => [...p, { type: "bot", text: `⚠ Error: ${err.message}`, isError: true }]);
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 0);
    }
  };

  const handleKeyDown = (e) => {
    if (showCommandPalette) {
      if (e.key === "ArrowDown") { e.preventDefault(); setActiveCmd((p) => (p < commands.length - 1 ? p + 1 : 0)); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setActiveCmd((p) => (p > 0 ? p - 1 : commands.length - 1)); }
      else if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); if (activeCmd >= 0) selectCommand(commands[activeCmd]); }
      else if (e.key === "Escape") { e.preventDefault(); setShowCommandPalette(false); }
      return;
    }
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const handleLogout = async () => {
    await clearSession(sessionId); clearSessionId(user?.id || "guest"); logout(); navigate("/login");
  };

  const handleNewChat = async () => {
    await clearSession(sessionId); clearSessionId(user?.id || "guest"); window.location.reload();
  };

  const badgeText = pendingLeaves != null
    ? pendingLeaves > 9 ? "9+" : String(pendingLeaves)
    : null;

  return (
    <div className="flex h-screen bg-[#0A0A0B]">

      {/* ── Sidebar — demo style, collapsible ───────────────────────────── */}
      <aside className={cn(
        "bg-white border-r border-slate-200 flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out",
        isCollapsed ? "w-[72px]" : "w-[240px]"
      )}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50/60">
          {!isCollapsed && (
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg overflow-hidden bg-black flex-shrink-0">
                <img src={LOGO} alt="NovaHR" className="w-full h-full object-cover" />
              </div>
              <div>
                <p className="font-semibold text-slate-800 text-sm leading-tight">NovaHR</p>
                <p className="text-xs text-slate-500">AI HR Assistant</p>
              </div>
            </div>
          )}
          {isCollapsed && (
            <div className="w-8 h-8 rounded-lg overflow-hidden bg-black mx-auto flex-shrink-0">
              <img src={LOGO} alt="NovaHR" className="w-full h-full object-cover" />
            </div>
          )}
          <button
            onClick={() => setIsCollapsed((p) => !p)}
            className="p-1.5 rounded-md hover:bg-slate-100 transition-colors"
          >
            {isCollapsed
              ? <ChevronRight className="w-4 h-4 text-slate-500" />
              : <ChevronLeft className="w-4 h-4 text-slate-500" />}
          </button>
        </div>

        {/* Search */}
        {!isCollapsed && (
          <div className="px-3 py-3">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search..."
                className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-2 py-1 overflow-y-auto">
          {/* New Chat */}
          <button
            onClick={handleNewChat}
            className={cn(
              "w-full flex items-center rounded-md text-left transition-all duration-200 group mb-1",
              "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
              isCollapsed ? "justify-center p-2.5" : "gap-2.5 px-3 py-2.5"
            )}
            title={isCollapsed ? "New Chat" : undefined}
          >
            <span className="text-lg leading-none flex-shrink-0">+</span>
            {!isCollapsed && <span className="text-sm">New Chat</span>}
          </button>

          {/* HR Dashboard — HR only */}
          {isHR && (
            <button
              onClick={() => navigate("/dashboard")}
              className={cn(
                "relative w-full flex items-center rounded-md text-left transition-all duration-200 group",
                "bg-blue-50 text-blue-700",
                isCollapsed ? "justify-center p-2.5" : "gap-2.5 px-3 py-2.5"
              )}
              title={isCollapsed ? "HR Dashboard" : undefined}
            >
              <LayoutDashboard className="w-4 h-4 flex-shrink-0 text-blue-600" />
              {!isCollapsed && (
                <div className="flex items-center justify-between w-full">
                  <span className="text-sm font-medium">HR Dashboard</span>
                  {badgeText && (
                    <span className="px-1.5 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
                      {badgeText}
                    </span>
                  )}
                </div>
              )}
              {/* Badge in collapsed state */}
              {isCollapsed && badgeText && (
                <span className="absolute top-1 right-1 w-4 h-4 flex items-center justify-center rounded-full bg-blue-100 border border-white text-[10px] font-medium text-blue-700">
                  {badgeText}
                </span>
              )}
              {/* Tooltip in collapsed state */}
              {isCollapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap z-50">
                  HR Dashboard
                  {badgeText && <span className="ml-1.5 px-1 py-0.5 bg-slate-700 rounded-full text-[10px]">{badgeText} pending</span>}
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 w-1.5 h-1.5 bg-slate-800 rotate-45" />
                </div>
              )}
            </button>
          )}
        </nav>

        {/* Bottom — profile + logout */}
        <div className="mt-auto border-t border-slate-200">
          {/* Profile */}
          <div className={cn("border-b border-slate-200 bg-slate-50/30", isCollapsed ? "py-3 px-2" : "p-3")}>
            {!isCollapsed ? (
              <div className="flex items-center px-3 py-2 rounded-md bg-white hover:bg-slate-50 transition-colors">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white font-medium text-sm">{user?.name?.charAt(0).toUpperCase() || "U"}</span>
                </div>
                <div className="flex-1 min-w-0 ml-2.5">
                  <p className="text-sm font-medium text-slate-800 truncate">{user?.name || "User"}</p>
                  <p className="text-xs text-slate-500 truncate">{user?.auth_role || "EMPLOYEE"}</p>
                </div>
                <div className="w-2 h-2 bg-green-500 rounded-full ml-2" title="Online" />
              </div>
            ) : (
              <div className="flex justify-center">
                <div className="relative">
                  <div className="w-9 h-9 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-medium text-sm">{user?.name?.charAt(0).toUpperCase() || "U"}</span>
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
                </div>
              </div>
            )}
          </div>

          {/* Logout */}
          <div className="p-3">
            <button
              onClick={handleLogout}
              className={cn(
                "w-full flex items-center rounded-md text-left transition-all duration-200 group",
                "text-red-600 hover:bg-red-50 hover:text-red-700",
                isCollapsed ? "justify-center p-2.5" : "gap-2.5 px-3 py-2.5"
              )}
              title={isCollapsed ? "Logout" : undefined}
            >
              <LogOut className="w-4 h-4 flex-shrink-0 text-red-500 group-hover:text-red-600" />
              {!isCollapsed && <span className="text-sm">Logout</span>}
              {isCollapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap z-50">
                  Logout
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 w-1.5 h-1.5 bg-slate-800 rotate-45" />
                </div>
              )}
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main ─────────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden relative">

        {/* Ambient blobs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full filter blur-[128px] animate-pulse" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full filter blur-[128px] animate-pulse" style={{ animationDelay: "700ms" }} />
          <div className="absolute top-1/4 right-1/3 w-64 h-64 bg-fuchsia-500/10 rounded-full filter blur-[96px] animate-pulse" style={{ animationDelay: "1000ms" }} />
        </div>

        {/* Header */}
        <header className="relative z-10 bg-zinc-900/60 backdrop-blur border-b border-white/[0.05] px-6 py-4 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full overflow-hidden bg-white flex-shrink-0">
              <img src={botAvatar} alt="NovaHR" className="w-full h-full object-contain" />
            </div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-white">NovaHR Assistant</h2>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-white/40">Online</span>
              </div>
            </div>
          </div>
        </header>

        {/* Messages */}
        <div className="relative z-10 flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {messages.map((msg, i) => (
            <ChatBubble key={i} message={msg.text} isBot={msg.type === "bot"}
              userInitial={user?.name?.charAt(0).toUpperCase() || "U"} />
          ))}

          {/* Thinking indicator — inline, appears where bot reply will be */}
          <AnimatePresence>
            {loading && (
              <motion.div
                className="flex gap-3 mb-4"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ duration: 0.2 }}
              >
                <div className="flex-shrink-0 w-9 h-9 rounded-full overflow-hidden bg-white">
                  <img src={botAvatar} alt="NovaHR Bot" className="w-full h-full object-contain" />
                </div>
                <div className="bg-zinc-800 border border-zinc-700 rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-2">
                  <span className="text-sm text-zinc-400">Thinking</span>
                  <TypingDots />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>

        {/* ── Input ────────────────────────────────────────────────────── */}
        <div className="relative z-10 flex-shrink-0 p-6">
          <div className="w-full max-w-2xl mx-auto">
            <motion.div
              className="relative backdrop-blur-2xl bg-white/[0.02] rounded-2xl border border-white/[0.05] shadow-2xl"
              initial={{ scale: 0.98 }} animate={{ scale: 1 }} transition={{ delay: 0.1 }}
            >
              {/* Command palette */}
              <AnimatePresence>
                {showCommandPalette && (
                  <motion.div
                    ref={commandPaletteRef}
                    className="absolute left-4 right-4 bottom-full mb-2 backdrop-blur-xl bg-black/90 rounded-xl z-50 shadow-2xl border border-white/10 overflow-hidden"
                    initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }}
                    transition={{ duration: 0.15 }}
                  >
                    <div className="px-3 py-2 border-b border-white/[0.06]">
                      <p className="text-xs text-white/30 font-medium uppercase tracking-wider">Quick Commands</p>
                    </div>
                    <div className="py-1">
                      {commands.map((cmd, i) => (
                        <motion.div key={cmd.label}
                          className={cn("flex items-start gap-3 px-3 py-2.5 cursor-pointer transition-colors",
                            activeCmd === i ? "bg-white/10" : "hover:bg-white/[0.05]")}
                          onClick={() => selectCommand(cmd)}
                          onMouseEnter={() => setActiveCmd(i)}
                          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                          transition={{ delay: i * 0.03 }}
                        >
                          <div className="mt-0.5 w-7 h-7 rounded-lg bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/60 flex-shrink-0">
                            {cmd.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-white/90 font-medium">{cmd.label}</p>
                            <p className="text-xs text-white/35 mt-0.5 leading-relaxed">{cmd.description}</p>
                          </div>
                          {activeCmd === i && (
                            <span className="flex-shrink-0 mt-1 text-[10px] text-white/25 bg-white/[0.05] px-1.5 py-0.5 rounded border border-white/[0.08]">↵</span>
                          )}
                        </motion.div>
                      ))}
                    </div>
                    <div className="px-3 py-2 border-t border-white/[0.06] flex items-center gap-3">
                      <span className="text-[10px] text-white/20">↑↓ navigate</span>
                      <span className="text-[10px] text-white/20">↵ select</span>
                      <span className="text-[10px] text-white/20">Esc close</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Textarea */}
              <div className="p-4">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => { setInput(e.target.value); adjustHeight(); }}
                  onKeyDown={handleKeyDown}
                  onFocus={() => setInputFocused(true)}
                  onBlur={() => setInputFocused(false)}
                  placeholder="Ask NovaHR a question..."
                  containerClassName="w-full"
                  className="w-full px-4 py-3 resize-none bg-transparent border-none text-white/90 text-sm focus:outline-none placeholder:text-white/20 min-h-[60px]"
                  style={{ overflow: "hidden" }}
                  showRing={false}
                  disabled={loading}
                />
              </div>

              {/* Toolbar */}
              <div className="p-4 border-t border-white/[0.05] flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <motion.button type="button" whileTap={{ scale: 0.94 }}
                    className="p-2 text-white/40 hover:text-white/90 rounded-lg transition-colors relative group" title="Attach file">
                    <Paperclip className="w-4 h-4" />
                    <motion.span className="absolute inset-0 bg-white/[0.05] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.button>
                  <motion.button type="button" data-command-button
                    onClick={(e) => { e.stopPropagation(); setShowCommandPalette((p) => !p); setActiveCmd(-1); }}
                    whileTap={{ scale: 0.94 }}
                    className={cn("p-2 rounded-lg transition-colors relative group",
                      showCommandPalette ? "bg-white/10 text-white/90" : "text-white/40 hover:text-white/90")}
                    title="Quick commands">
                    <Command className="w-4 h-4" />
                    <motion.span className="absolute inset-0 bg-white/[0.05] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.button>
                </div>
                <motion.button type="button" onClick={handleSend}
                  whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }}
                  disabled={loading || !input.trim()}
                  className={cn("px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                    input.trim() && !loading ? "bg-white text-[#0A0A0B] shadow-lg shadow-white/10" : "bg-white/[0.05] text-white/40")}>
                  {loading ? <LoaderIcon className="w-4 h-4 animate-[spin_2s_linear_infinite]" /> : <SendIcon className="w-4 h-4" />}
                  <span>Send</span>
                </motion.button>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Mouse glow */}
        {inputFocused && (
          <motion.div
            className="fixed w-[50rem] h-[50rem] rounded-full pointer-events-none z-0 opacity-[0.02] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-indigo-500 blur-[96px]"
            animate={{ x: mousePosition.x - 400, y: mousePosition.y - 400 }}
            transition={{ type: "spring", damping: 25, stiffness: 150, mass: 0.5 }}
          />
        )}
      </main>
    </div>
  );
}

