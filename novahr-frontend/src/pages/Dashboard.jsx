import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getLeaves, getLeaveStats, approveLeave, rejectLeave } from "../services/leaveService";
import { logout, getUser } from "../services/authService";
import { clearSession } from "../services/chatService";
import { getOrCreateSessionId, clearSessionId } from "../utils/session";
import {
  getAllUsersMemories,
  getMemoryStats,
  clearUserMemories,
  triggerCleanup,
  cleanupOldMemories,
} from "../services/memoryService";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function Dashboard() {
  const navigate = useNavigate();
  const [leaves, setLeaves] = useState([]);
  const [stats, setStats] = useState({ total: 0, pending: 0, approved: 0, rejected: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [filter, setFilter] = useState("all");
  const [toast, setToast] = useState(null);

  // Memory section state
  const [memoryStats, setMemoryStats] = useState(null);
  const [memoriesByUser, setMemoriesByUser] = useState({});
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [memoryError, setMemoryError] = useState(null);
  const [expandedUser, setExpandedUser] = useState(null);
  const [cleanupDays, setCleanupDays] = useState(30);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [clearingUser, setClearingUser] = useState(null);
  const [confirmClear, setConfirmClear] = useState(null); // userId to confirm clear

  const user = getUser();
  const sessionId = getOrCreateSessionId(user?.id || "guest");

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Run independently so one failure doesn't block the other
      const [leavesResult, statsResult] = await Promise.allSettled([
        getLeaves(),
        getLeaveStats(),
      ]);

      if (leavesResult.status === "fulfilled") {
        setLeaves(leavesResult.value);
      } else {
        console.error("Leaves fetch error:", leavesResult.reason);
        setError(leavesResult.reason?.message || "Failed to load leave requests");
      }

      if (statsResult.status === "fulfilled") {
        setStats(statsResult.value);
      } else {
        console.error("Stats fetch error:", statsResult.reason);
      }
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleApprove = async (leaveId) => {
    setActionLoading(leaveId);
    try {
      await approveLeave(leaveId);
      setLeaves((prev) =>
        prev.map((l) => (l.leave_id === leaveId ? { ...l, status: "approved" } : l))
      );
      setStats((prev) => ({ ...prev, pending: prev.pending - 1, approved: prev.approved + 1 }));
      showToast("Leave approved successfully", "success");
    } catch (err) {
      showToast("Failed to approve leave", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (leaveId) => {
    setActionLoading(leaveId);
    try {
      await rejectLeave(leaveId);
      setLeaves((prev) =>
        prev.map((l) => (l.leave_id === leaveId ? { ...l, status: "rejected" } : l))
      );
      setStats((prev) => ({ ...prev, pending: prev.pending - 1, rejected: prev.rejected + 1 }));
      showToast("Leave rejected", "error");
    } catch (err) {
      showToast("Failed to reject leave", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleLogout = async () => {
    await clearSession(sessionId);
    clearSessionId(user?.id || "guest");
    logout();
    navigate("/login");
  };

  // ── Memory section handlers ──────────────────────────────────────
  const fetchMemories = async () => {
    setMemoryLoading(true);
    setMemoryError(null);
    try {
      const [statsResult, allResult] = await Promise.allSettled([
        getMemoryStats(),
        getAllUsersMemories(),
      ]);

      if (statsResult.status === "fulfilled") {
        setMemoryStats(statsResult.value);
      }
      if (allResult.status === "fulfilled") {
        setMemoriesByUser(allResult.value.memories_by_user || {});
      } else {
        setMemoryError(allResult.reason?.message || "Failed to load memories");
      }
    } catch (err) {
      setMemoryError(err.message);
    } finally {
      setMemoryLoading(false);
    }
  };

  const handleTriggerCleanup = async () => {
    setCleanupLoading(true);
    try {
      const result = await cleanupOldMemories(cleanupDays);
      showToast(
        `Cleanup done — deleted ${result.deleted} memories older than ${cleanupDays} days`,
        "success"
      );
      fetchMemories();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setCleanupLoading(false);
    }
  };

  const handleClearUser = async (userId) => {
    setClearingUser(userId);
    try {
      await clearUserMemories(userId);
      showToast(`Cleared all memories for user ${userId}`, "success");
      setConfirmClear(null);
      fetchMemories();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setClearingUser(null);
    }
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  const filteredLeaves = leaves.filter((l) =>
    filter === "all" ? true : l.status === filter
  );

  // Chart data
  const chartData = [
    { name: 'Pending', value: stats.pending, fill: '#f59e0b' },
    { name: 'Approved', value: stats.approved, fill: '#10b981' },
    { name: 'Rejected', value: stats.rejected, fill: '#ef4444' },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-zinc-900 text-white flex flex-col">
        <div className="p-4 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0">
              <img src="/bot-avatar.png" alt="NovaHR" className="w-full h-full object-contain" />
            </div>
            <span className="text-xl font-bold">NovaHR</span>
          </div>
        </div>

        <div className="flex-1 px-4 py-6 space-y-2">
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-3">Navigation</p>
          <button
            onClick={() => navigate("/chat")}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-sm"
          >
            💬 AI Assistant
          </button>
          <button className="w-full text-left px-3 py-2 rounded-lg bg-zinc-800 text-sm">
            📊 HR Dashboard
          </button>
        </div>

        <div className="p-4 border-t border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center font-bold">
              {user?.name?.charAt(0).toUpperCase() || "H"}
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium">{user?.name || "HR"}</span>
              <span className="text-xs text-gray-400">{user?.auth_role || "HR"}</span>
            </div>
          </div>
          <button onClick={handleLogout} className="text-gray-400 hover:text-white transition-colors" title="Logout">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-8 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Leave Requests</h1>
            <p className="text-gray-600 text-sm mt-1">Review and manage employee leave applications</p>
          </div>
          <button
            onClick={fetchData}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </header>

        <div className="p-8 space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-4 gap-6">
            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                  📋
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 border border-orange-200 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center text-2xl">
                  ⏳
                </div>
                <div>
                  <p className="text-sm text-gray-600">Pending</p>
                  <p className="text-3xl font-bold text-orange-600">{stats.pending}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 border border-green-200 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl">
                  ✅
                </div>
                <div>
                  <p className="text-sm text-gray-600">Approved</p>
                  <p className="text-3xl font-bold text-green-600">{stats.approved}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 border border-red-200 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center text-2xl">
                  ❌
                </div>
                <div>
                  <p className="text-sm text-gray-600">Rejected</p>
                  <p className="text-3xl font-bold text-red-600">{stats.rejected}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Leave Status Overview</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Filter Tabs */}
          <div className="flex gap-2 bg-white rounded-xl p-2 border border-gray-200">
            {["all", "pending", "approved", "rejected"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                  filter === f
                    ? "bg-blue-600 text-white shadow-md"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
                <span className={`ml-2 text-sm ${filter === f ? "text-blue-100" : "text-gray-400"}`}>
                  ({f === "all" ? leaves.length : leaves.filter((l) => l.status === f).length})
                </span>
              </button>
            ))}
          </div>

          {/* Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {loading ? (
              <div className="p-12 text-center text-gray-500">Loading leave requests...</div>
            ) : error ? (
              <div className="p-12 text-center">
                <p className="text-red-600 mb-4">⚠ {error}</p>
                <button onClick={fetchData} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                  Try Again
                </button>
              </div>
            ) : filteredLeaves.length === 0 ? (
              <div className="p-12 text-center text-gray-500">
                No {filter === "all" ? "" : filter} leave requests found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Employee</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">From</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">To</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Days</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredLeaves.map((leave) => (
                      <tr key={leave.leave_id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                              {leave.name?.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <p className="text-sm font-medium text-gray-900">{leave.name}</p>
                              <p className="text-sm text-gray-500">{leave.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            leave.leave_type === 'EL' ? 'bg-indigo-100 text-indigo-800' :
                            leave.leave_type === 'CL' ? 'bg-cyan-100 text-cyan-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            {leave.leave_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{leave.start_date}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{leave.end_date}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{leave.days}d</td>
                        <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">{leave.reason || "—"}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            leave.status === 'pending' ? 'bg-orange-100 text-orange-800' :
                            leave.status === 'approved' ? 'bg-green-100 text-green-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {leave.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {leave.status === "pending" ? (
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleApprove(leave.leave_id)}
                                disabled={actionLoading === leave.leave_id}
                                className="bg-green-600 text-white px-3 py-1 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors text-xs font-medium"
                              >
                                {actionLoading === leave.leave_id ? "..." : "Approve"}
                              </button>
                              <button
                                onClick={() => handleReject(leave.leave_id)}
                                disabled={actionLoading === leave.leave_id}
                                className="bg-red-600 text-white px-3 py-1 rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors text-xs font-medium"
                              >
                                {actionLoading === leave.leave_id ? "..." : "Reject"}
                              </button>
                            </div>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* ── Memory Management Section (HR only) ─────────────────── */}
        <div className="p-8 pt-0">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {/* Section Header */}
            <div className="px-6 py-5 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-xl">
                  🧠
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Memory Management</h2>
                  <p className="text-sm text-gray-500">
                    View and manage long-term AI memory stored per employee
                  </p>
                </div>
              </div>
              <button
                onClick={fetchMemories}
                disabled={memoryLoading}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors text-sm font-medium"
              >
                {memoryLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
                {memoryLoading ? "Loading..." : "Load Memories"}
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Stats row */}
              {memoryStats && (
                <div className="flex items-center gap-6 p-4 bg-purple-50 rounded-xl border border-purple-100">
                  <div className="text-center">
                    <p className="text-3xl font-bold text-purple-700">{memoryStats.total_memories}</p>
                    <p className="text-xs text-purple-500 mt-1">Total Memories</p>
                  </div>
                  <div className="h-10 w-px bg-purple-200" />
                  <div className="text-center">
                    <p className="text-3xl font-bold text-purple-700">{Object.keys(memoriesByUser).length}</p>
                    <p className="text-xs text-purple-500 mt-1">Users with Memory</p>
                  </div>
                  <div className="h-10 w-px bg-purple-200" />
                  <div className="text-sm text-purple-600">
                    Auto-cleanup runs daily at 2 AM (removes memories older than 30 days)
                  </div>
                </div>
              )}

              {/* Error */}
              {memoryError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
                  ⚠ {memoryError}
                </div>
              )}

              {/* Not loaded yet */}
              {!memoryStats && !memoryLoading && !memoryError && (
                <div className="text-center py-8 text-gray-400">
                  <p className="text-4xl mb-3">🧠</p>
                  <p className="text-sm">Click "Load Memories" to view stored memories</p>
                </div>
              )}

              {/* Per-user memory list */}
              {Object.keys(memoriesByUser).length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                    Memories by Employee
                  </h3>
                  {Object.entries(memoriesByUser).map(([userId, memories]) => (
                    <div key={userId} className="border border-gray-200 rounded-xl overflow-hidden">
                      {/* User row */}
                      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors">
                        <button
                          className="flex items-center gap-3 flex-1 text-left"
                          onClick={() => setExpandedUser(expandedUser === userId ? null : userId)}
                        >
                          <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white text-sm font-bold">
                            {userId}
                          </div>
                          <div>
                            <span className="text-sm font-medium text-gray-900">User ID: {userId}</span>
                            <span className="ml-3 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                              {memories.length} {memories.length === 1 ? "memory" : "memories"}
                            </span>
                          </div>
                          <svg
                            className={`w-4 h-4 text-gray-400 ml-auto transition-transform ${expandedUser === userId ? "rotate-180" : ""}`}
                            fill="none" stroke="currentColor" viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>

                        {/* Clear button */}
                        {confirmClear === userId ? (
                          <div className="flex items-center gap-2 ml-4">
                            <span className="text-xs text-red-600 font-medium">Confirm?</span>
                            <button
                              onClick={() => handleClearUser(userId)}
                              disabled={clearingUser === userId}
                              className="px-3 py-1 bg-red-600 text-white text-xs rounded-lg hover:bg-red-700 disabled:opacity-50"
                            >
                              {clearingUser === userId ? "..." : "Yes, Clear"}
                            </button>
                            <button
                              onClick={() => setConfirmClear(null)}
                              className="px-3 py-1 bg-gray-200 text-gray-700 text-xs rounded-lg hover:bg-gray-300"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setConfirmClear(userId)}
                            className="ml-4 px-3 py-1 text-xs text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
                          >
                            Clear
                          </button>
                        )}
                      </div>

                      {/* Expanded memory list */}
                      {expandedUser === userId && (
                        <div className="divide-y divide-gray-100">
                          {memories.map((mem, idx) => (
                            <div key={idx} className="px-4 py-3 flex items-start gap-3">
                              <div className="mt-0.5 w-2 h-2 rounded-full bg-purple-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-gray-800 break-words">{mem.text}</p>
                                <div className="flex items-center gap-3 mt-1">
                                  <span className="text-xs text-gray-400">{formatDate(mem.timestamp)}</span>
                                  {mem.intent && (
                                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full">
                                      {mem.intent}
                                    </span>
                                  )}
                                  {mem.type && (
                                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">
                                      {mem.type}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Empty state after load */}
              {memoryStats && Object.keys(memoriesByUser).length === 0 && (
                <div className="text-center py-8 text-gray-400">
                  <p className="text-4xl mb-3">🧹</p>
                  <p className="text-sm">No memories stored yet</p>
                </div>
              )}

              {/* Cleanup Controls */}
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
                  Cleanup Controls
                </h3>
                <div className="flex items-center gap-4 flex-wrap">
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600 whitespace-nowrap">Delete memories older than</label>
                    <input
                      type="number"
                      min={0}
                      max={365}
                      value={cleanupDays}
                      onChange={(e) => setCleanupDays(Number(e.target.value))}
                      className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                    <span className="text-sm text-gray-600">
                      {cleanupDays === 0 ? "days (delete ALL)" : "days"}
                    </span>
                  </div>
                  <button
                    onClick={handleTriggerCleanup}
                    disabled={cleanupLoading}
                    className="flex items-center gap-2 px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors text-sm font-medium"
                  >
                    {cleanupLoading ? (
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    )}
                    {cleanupLoading ? "Running..." : "Run Cleanup"}
                  </button>
                  <p className="text-xs text-gray-400">
                    This permanently deletes old memories. Auto-cleanup also runs daily at 2 AM.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 px-6 py-4 rounded-xl shadow-2xl animate-slide-up ${
          toast.type === "success" ? "bg-green-600" : "bg-red-600"
        } text-white font-medium`}>
          {toast.type === "success" ? "✓" : "✗"} {toast.message}
        </div>
      )}
    </div>
  );
}
