import { useState, useEffect } from "react";
import { getLeaves, getLeaveStats, approveLeave, rejectLeave } from "../services/leaveService";
import { logout, getUser } from "../services/authService";
import "./Dashboard.css";

export default function Dashboard() {
  const [leaves, setLeaves] = useState([]);
  const [stats, setStats] = useState({ total: 0, pending: 0, approved: 0, rejected: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(null); // leave_id being actioned
  const [filter, setFilter] = useState("all");
  const [toast, setToast] = useState(null);

  const user = getUser();

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [leavesData, statsData] = await Promise.all([getLeaves(), getLeaveStats()]);
      setLeaves(leavesData);
      setStats(statsData);
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

  const filteredLeaves = leaves.filter((l) =>
    filter === "all" ? true : l.status === filter
  );

  const leaveTypeBadge = (type) => {
    const map = { EL: "#6366f1", CL: "#0ea5e9", SL: "#f59e0b" };
    return map[type] || "#6b7280";
  };

  return (
    <div className="dash-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">💼</span>
          <span className="sidebar-title">NovaHR</span>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">Navigation</p>
          <button className="quick-btn" onClick={() => (window.location.href = "/chat")}>
            💬 AI Assistant
          </button>
          <button className="quick-btn active-nav">
            📊 HR Dashboard
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.name?.charAt(0).toUpperCase() || "H"}
            </div>
            <div className="user-details">
              <span className="user-name">{user?.name || "HR"}</span>
              <span className="user-role">{user?.auth_role || "HR"}</span>
            </div>
          </div>
          <button className="logout-btn" onClick={logout} title="Logout">⎋</button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="dash-main">
        {/* Header */}
        <header className="dash-header">
          <div>
            <h1>Leave Requests</h1>
            <p>Review and manage employee leave applications</p>
          </div>
          <button className="refresh-btn" onClick={fetchData}>↻ Refresh</button>
        </header>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-icon">📋</span>
            <div>
              <p className="stat-label">Total</p>
              <p className="stat-value">{stats.total}</p>
            </div>
          </div>
          <div className="stat-card pending">
            <span className="stat-icon">⏳</span>
            <div>
              <p className="stat-label">Pending</p>
              <p className="stat-value">{stats.pending}</p>
            </div>
          </div>
          <div className="stat-card approved">
            <span className="stat-icon">✅</span>
            <div>
              <p className="stat-label">Approved</p>
              <p className="stat-value">{stats.approved}</p>
            </div>
          </div>
          <div className="stat-card rejected">
            <span className="stat-icon">❌</span>
            <div>
              <p className="stat-label">Rejected</p>
              <p className="stat-value">{stats.rejected}</p>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="filter-tabs">
          {["all", "pending", "approved", "rejected"].map((f) => (
            <button
              key={f}
              className={`filter-tab ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              <span className="tab-count">
                {f === "all" ? leaves.length : leaves.filter((l) => l.status === f).length}
              </span>
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="table-wrapper">
          {loading ? (
            <div className="table-empty">Loading leave requests...</div>
          ) : error ? (
            <div className="table-error">
              <p>⚠ {error}</p>
              <button className="refresh-btn" style={{marginTop: "12px"}} onClick={fetchData}>Try Again</button>
            </div>
          ) : filteredLeaves.length === 0 ? (
            <div className="table-empty">No {filter === "all" ? "" : filter} leave requests found.</div>
          ) : (
            <table className="leave-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Type</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Days</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredLeaves.map((leave) => (
                  <tr key={leave.leave_id}>
                    <td>
                      <div className="employee-cell">
                        <div className="emp-avatar">
                          {leave.name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="emp-name">{leave.name}</p>
                          <p className="emp-email">{leave.email}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span
                        className="type-badge"
                        style={{ background: leaveTypeBadge(leave.leave_type) }}
                      >
                        {leave.leave_type}
                      </span>
                    </td>
                    <td>{leave.start_date}</td>
                    <td>{leave.end_date}</td>
                    <td className="days-cell">{leave.days}d</td>
                    <td className="reason-cell">{leave.reason || "—"}</td>
                    <td>
                      <span className={`status-badge status-${leave.status}`}>
                        {leave.status}
                      </span>
                    </td>
                    <td>
                      {leave.status === "pending" ? (
                        <div className="action-btns">
                          <button
                            className="btn-approve"
                            onClick={() => handleApprove(leave.leave_id)}
                            disabled={actionLoading === leave.leave_id}
                          >
                            {actionLoading === leave.leave_id ? "..." : "Approve"}
                          </button>
                          <button
                            className="btn-reject"
                            onClick={() => handleReject(leave.leave_id)}
                            disabled={actionLoading === leave.leave_id}
                          >
                            {actionLoading === leave.leave_id ? "..." : "Reject"}
                          </button>
                        </div>
                      ) : (
                        <span className="no-action">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Toast Notification */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.type === "success" ? "✓" : "✗"} {toast.message}
        </div>
      )}
    </div>
  );
}
