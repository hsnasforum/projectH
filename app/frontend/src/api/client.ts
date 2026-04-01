import type { ChatResponse, SessionSummary, Session, StreamEvent } from "../types";

const BASE = "";

export async function fetchSessions(): Promise<SessionSummary[]> {
  const res = await fetch(`${BASE}/api/sessions`);
  const data = await res.json();
  return data.sessions ?? [];
}

export async function fetchSession(sessionId: string): Promise<Session> {
  const res = await fetch(`${BASE}/api/session?session_id=${encodeURIComponent(sessionId)}`);
  const data = await res.json();
  return data.session;
}

export async function postChat(payload: Record<string, unknown>): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function* streamChat(
  payload: Record<string, unknown>,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        yield JSON.parse(trimmed) as StreamEvent;
      } catch {
        // skip malformed lines
      }
    }
  }
  if (buffer.trim()) {
    try {
      yield JSON.parse(buffer.trim()) as StreamEvent;
    } catch {
      // skip
    }
  }
}

export async function cancelChat(sessionId: string, requestId: string): Promise<void> {
  await fetch(`${BASE}/api/chat/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, request_id: requestId }),
  });
}

export async function postFeedback(
  sessionId: string,
  messageId: string,
  label: string,
  reason?: string,
): Promise<void> {
  await fetch(`${BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, feedback_label: label, feedback_reason: reason }),
  });
}

export async function postCorrection(
  sessionId: string,
  messageId: string,
  correctedText: string,
): Promise<void> {
  await fetch(`${BASE}/api/correction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, corrected_text: correctedText }),
  });
}
