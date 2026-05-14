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

/** Bulk add employees from Excel file — HR only. Returns upload summary. */
export async function uploadEmployees(file) {
  const token = localStorage.getItem("token");
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/employees/bulk`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (res.status === 401) {
    localStorage.clear();
    window.location.href = "/";
    throw new Error("Session expired.");
  }
  if (res.status === 403) throw new Error("Access denied. HR role required.");
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(body.detail || `Server error: ${res.status}`);
  }
  return res.json();
}

/**
 * Bulk add employees with real-time SSE streaming.
 * Calls onProgress(event) for each row, onDone(summary) when complete.
 * Returns a cleanup function to abort the stream.
 */
export function streamUploadEmployees(file, onProgress, onDone, onError) {
  const token = localStorage.getItem("token");
  const formData = new FormData();
  formData.append("file", file);

  const controller = new AbortController();

  fetch(`${API_BASE}/api/employees/bulk/stream`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: "Upload failed" }));
        onError(body.detail || `Server error: ${res.status}`);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // keep incomplete chunk

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          try {
            const event = JSON.parse(trimmed.slice(5).trim());
            if (event.type === "progress") onProgress(event);
            else if (event.type === "done") onDone(event);
          } catch (_) {}
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") onError(err.message);
    });

  return () => controller.abort();
}
