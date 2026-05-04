const API_BASE = "http://localhost:8000";

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
  const token = localStorage.getItem("token");
  console.log("Fetching leaves with token:", token ? token.substring(0, 30) + "..." : "NO TOKEN");
  
  try {
    const res = await fetch(`${API_BASE}/api/leaves`, {
      headers: authHeaders(),
    });
    console.log("GET /api/leaves status:", res.status);
    return handleResponse(res);
  } catch (err) {
    if (err.message.includes("fetch")) {
      throw new Error("Cannot connect to server. Is the backend running on port 8000?");
    }
    throw err;
  }
}

export async function getLeaveStats() {
  try {
    const res = await fetch(`${API_BASE}/api/leaves/stats`, {
      headers: authHeaders(),
    });
    console.log("GET /api/leaves/stats status:", res.status);
    return handleResponse(res);
  } catch (err) {
    if (err.message.includes("fetch")) {
      throw new Error("Cannot connect to server. Is the backend running on port 8000?");
    }
    throw err;
  }
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
