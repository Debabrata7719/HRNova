import API_BASE from "../config/api";

export async function sendMessage(message, sessionId) {
  const token = localStorage.getItem("token");

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId,
    }),
  });

  if (response.status === 401) {
    localStorage.clear();
    window.location.href = "/";
    return;
  }

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Something went wrong");
  }

  return await response.json();
}

export async function clearSession(sessionId) {
  const token = localStorage.getItem("token");

  await fetch(`${API_BASE}/api/chat/session/${sessionId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}
