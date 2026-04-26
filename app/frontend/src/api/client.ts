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

// -- Candidate review API --

export async function postCandidateReview(
  sessionId: string,
  messageId: string,
  candidateId: string,
  candidateUpdatedAt: string,
  action: "accept" | "reject" | "defer",
  statement?: string,
  reasonNote?: string,
): Promise<void> {
  await fetch(`${BASE}/api/candidate-review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message_id: messageId,
      candidate_id: candidateId,
      candidate_updated_at: candidateUpdatedAt,
      review_action: action,
      ...(statement !== undefined ? { statement } : {}),
      ...(reasonNote ? { reason_note: reasonNote } : {}),
    }),
  });
}

export async function postCorrectedSave(
  sessionId: string,
  messageId: string,
): Promise<ChatResponse> {
  return postChat({ session_id: sessionId, corrected_save_message_id: messageId });
}

export async function postContentVerdict(
  sessionId: string,
  messageId: string,
  contentVerdict: string,
): Promise<Record<string, unknown>> {
  const resp = await fetch(`${BASE}/api/content-verdict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message_id: messageId,
      content_verdict: contentVerdict,
    }),
  });
  return resp.json();
}

export async function postContentReasonNote(
  sessionId: string,
  messageId: string,
  reasonNote: string,
): Promise<Record<string, unknown>> {
  const resp = await fetch(`${BASE}/api/content-reason-note`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message_id: messageId,
      reason_note: reasonNote,
    }),
  });
  return resp.json();
}

export async function postContentReasonLabel(
  sessionId: string,
  messageId: string,
  reasonLabel: string,
): Promise<Record<string, unknown>> {
  const resp = await fetch(`${BASE}/api/content-reason-label`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message_id: messageId,
      reason_label: reasonLabel,
    }),
  });
  return resp.json();
}

// -- Session management API --

export async function deleteSession(sessionId: string): Promise<{ ok: boolean; deleted: boolean }> {
  const res = await fetch(`${BASE}/api/sessions/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return res.json();
}

export async function deleteAllSessions(): Promise<{ ok: boolean; deleted_count: number }> {
  const res = await fetch(`${BASE}/api/sessions/delete-all`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  return res.json();
}

// -- Preferences API --

export interface PreferenceRecord {
  preference_id: string;
  delta_fingerprint: string;
  description: string;
  status: string;
  evidence_count: number;
  cross_session_count: number;
  reliability_stats?: {
    applied_count?: number | null;
    corrected_count?: number | null;
  } | null;
  quality_info?: {
    avg_similarity_score: number | null;
    is_high_quality: boolean | null;
  } | null;
  review_reason_note?: string | null;
  last_transition_reason?: string | null;
  source_session_title?: string | null;
  activated_at: string | null;
  created_at: string;
  updated_at: string;
  delta_summary?: {
    additions?: string[];
    removals?: string[];
    replacements?: Array<{ from: string; to: string }>;
  };
  original_snippet?: string | null;
  corrected_snippet?: string | null;
  conflict_info?: {
    has_conflict: boolean;
    conflicting_preference_ids: string[];
  } | null;
}

export interface ReviewQueueItem {
  item_type: string;
  candidate_id: string;
  candidate_scope: string;
  candidate_family: string;
  statement: string;
  derived_from: Record<string, unknown>;
  derived_at: string;
  promotion_basis: string;
  promotion_eligibility: string;
  artifact_id: string;
  source_message_id: string;
  source_session_id?: string | null;
  source_session_title?: string | null;
  supporting_artifact_ids: string[];
  supporting_source_message_ids: string[];
  supporting_signal_refs: Record<string, unknown>[];
  supporting_confirmation_refs: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
  quality_info: {
    avg_similarity_score: number | null;
    is_high_quality: boolean | null;
  } | null;
  delta_summary?: {
    additions?: string[];
    removals?: string[];
    replacements?: Array<{ from: string; to: string }>;
  } | null;
  original_snippet?: string | null;
  corrected_snippet?: string | null;
  context_turns?: Array<{
    role: string;
    text: string;
    message_id?: string | null;
  }> | null;
  evidence_summary?: {
    artifact_count: number;
    signal_count: number;
    confirmation_count: number;
    recurring_session_count: number;
  } | null;
  is_global?: boolean | null;
}

export interface PreferencesPayload {
  ok: boolean;
  preferences: PreferenceRecord[];
  active_count: number;
  candidate_count: number;
  paused_count: number;
  total_applied?: number | null;
  total_corrected?: number | null;
}

export async function fetchPreferences(): Promise<PreferencesPayload> {
  const res = await fetch(`${BASE}/api/preferences`);
  return res.json();
}

export interface PreferenceAudit {
  total: number;
  by_status: Record<string, number>;
  conflict_pair_count: number;
  adopted_corrections_count?: number;
  available_to_sync_count?: number;
}

export interface SyncAdoptedPreferenceCandidatesResponse {
  ok: boolean;
  synced_count: number;
  skipped_count: number;
}

export async function fetchPreferenceAudit(): Promise<PreferenceAudit | null> {
  const res = await fetch(`${BASE}/api/preferences/audit`);
  if (!res.ok) return null;
  const data = await res.json();
  return data.audit ?? null;
}

export async function postSyncAdoptedToPreferenceCandidates(): Promise<SyncAdoptedPreferenceCandidatesResponse> {
  const res = await fetch(`${BASE}/api/corrections/sync-adopted-to-candidates`, {
    method: "POST",
  });
  return res.json();
}

export async function activatePreference(
  preferenceId: string,
  transitionReason?: string,
): Promise<{ ok: boolean; preference: PreferenceRecord }> {
  const res = await fetch(`${BASE}/api/preferences/activate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      preference_id: preferenceId,
      ...(transitionReason ? { transition_reason: transitionReason } : {}),
    }),
  });
  return res.json();
}

export async function pausePreference(
  preferenceId: string,
  transitionReason?: string,
): Promise<{ ok: boolean; preference: PreferenceRecord }> {
  const res = await fetch(`${BASE}/api/preferences/pause`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      preference_id: preferenceId,
      ...(transitionReason ? { transition_reason: transitionReason } : {}),
    }),
  });
  return res.json();
}

export async function rejectPreference(
  preferenceId: string,
  transitionReason?: string,
): Promise<{ ok: boolean; preference: PreferenceRecord }> {
  const res = await fetch(`${BASE}/api/preferences/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      preference_id: preferenceId,
      ...(transitionReason ? { transition_reason: transitionReason } : {}),
    }),
  });
  return res.json();
}

export async function updatePreferenceDescription(
  preferenceId: string,
  description: string,
): Promise<{ ok: boolean; preference: PreferenceRecord }> {
  const res = await fetch(`${BASE}/api/preferences/update-description`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preference_id: preferenceId, description }),
  });
  return res.json();
}
