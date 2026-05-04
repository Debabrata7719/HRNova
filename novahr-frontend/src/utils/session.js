export function generateSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function getOrCreateSessionId(userId) {
  const key = `session_id_${userId}`;
  let sessionId = sessionStorage.getItem(key);
  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem(key, sessionId);
  }
  return sessionId;
}

export function clearSessionId(userId) {
  sessionStorage.removeItem(`session_id_${userId}`);
}
