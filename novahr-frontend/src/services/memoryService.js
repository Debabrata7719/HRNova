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
    throw new Error(`Server error: ${res.status} - ${body}`);
  }
  return res.json();
}

/** Get total memory stats */
export async function getMemoryStats() {
  const res = await fetch(`${API_BASE}/api/memory/stats`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

/** Get all users' memories — HR only */
export async function getAllUsersMemories() {
  const res = await fetch(`${API_BASE}/api/memory/all`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

/** Clear memories for a specific user — HR only */
export async function clearUserMemories(userId) {
  const res = await fetch(`${API_BASE}/api/memory/user/${userId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  return handleResponse(res);
}

/** Trigger immediate cleanup (30 days) — HR only */
export async function triggerCleanup() {
  const res = await fetch(`${API_BASE}/api/memory/cleanup/trigger`, {
    method: "POST",
    headers: authHeaders(),
  });
  return handleResponse(res);
}

/** Custom cleanup with specific days — HR only */
export async function cleanupOldMemories(days = 30) {
  const res = await fetch(`${API_BASE}/api/memory/cleanup`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ days }),
  });
  return handleResponse(res);
}
