import API_BASE from "../config/api";

function authHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function handleResponse(res) {
  if (res.status === 401) {
    localStorage.clear();
    window.location.href = "/";
    throw new Error("Session expired. Please login again.");
  }
  if (res.status === 403) {
    throw new Error("Access denied. HR role required.");
  }
  if (!res.ok) {
    const body = await res.text();
    console.error("API Error body:", body);
    throw new Error(`Server error: ${res.status} - ${body}`);
  }
  return res.json();
}

export async function getLeaves() {
  const res = await fetch(`${API_BASE}/api/leaves`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function getLeaveStats() {
  const res = await fetch(`${API_BASE}/api/leaves/stats`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function approveLeave(leaveId) {
  const res = await fetch(`${API_BASE}/api/leaves/${leaveId}/approve`, {
    method: "PUT",
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function rejectLeave(leaveId) {
  const res = await fetch(`${API_BASE}/api/leaves/${leaveId}/reject`, {
    method: "PUT",
    headers: authHeaders(),
  });
  return handleResponse(res);
}
