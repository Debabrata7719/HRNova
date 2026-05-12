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
    const body = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(body.detail || `Server error: ${res.status}`);
  }
  return res.json();
}

/** Add a new employee — HR only. Returns employee data + generated password. */
export async function addEmployee(name, email, department, role) {
  const res = await fetch(`${API_BASE}/api/employees`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ name, email, department, role }),
  });
  return handleResponse(res);
}
