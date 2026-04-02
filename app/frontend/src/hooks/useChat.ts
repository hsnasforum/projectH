import { useState, useEffect, useCallback, useRef } from "react";
import type { Message, SessionSummary, PendingApproval, AppSettings } from "../types";
import { fetchSessions, fetchSession, streamChat, deleteSession as apiDeleteSession, deleteAllSessions as apiDeleteAllSessions } from "../api/client";

const DEFAULT_SESSION = "demo-session";

/** Per-session state kept in a Map so background sessions stay alive. */
interface SessionState {
  messages: Message[];
  pendingApproval: PendingApproval | null;
  streamingText: string;
  isStreaming: boolean;
  thinkingStatus: string;
  title: string;
  abort: AbortController | null;
  justCompleted: boolean;
  reviewQueueCount: number;
}

function emptyState(title: string): SessionState {
  return {
    messages: [],
    pendingApproval: null,
    streamingText: "",
    isStreaming: false,
    thinkingStatus: "",
    title,
    abort: null,
    justCompleted: false,
    reviewQueueCount: 0,
  };
}

export function useChat(settings: AppSettings) {
  const [sessionId, setSessionId] = useState(DEFAULT_SESSION);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [notifications, setNotifications] = useState<{ id: string; title: string; sid: string }[]>([]);
  const activeSessionRef = useRef(DEFAULT_SESSION);

  // Map of session states — survives session switches
  const statesRef = useRef<Map<string, SessionState>>(new Map());
  // Force re-render counter
  const [, setTick] = useState(0);
  const rerender = useCallback(() => setTick((t) => t + 1), []);

  const getState = useCallback((sid: string): SessionState => {
    let s = statesRef.current.get(sid);
    if (!s) {
      s = emptyState(sid);
      statesRef.current.set(sid, s);
    }
    return s;
  }, []);

  const updateState = useCallback((sid: string, patch: Partial<SessionState>) => {
    const s = getState(sid);
    Object.assign(s, patch);
    rerender();
  }, [getState, rerender]);

  const loadSessions = useCallback(async () => {
    const list = await fetchSessions();
    setSessions(list);
  }, []);

  const loadSession = useCallback(async (sid: string) => {
    const session = await fetchSession(sid);
    const approvals = session.pending_approvals ?? [];
    updateState(sid, {
      messages: session.messages,
      title: session.title,
      pendingApproval: approvals.length > 0 ? approvals[approvals.length - 1] : null,
      reviewQueueCount: (session.review_queue_items ?? []).length,
    });
  }, [updateState]);

  useEffect(() => {
    loadSessions();
    loadSession(sessionId);
  }, [sessionId, loadSessions, loadSession]);

  const switchSession = useCallback((sid: string) => {
    // Don't abort anything — background session keeps running
    activeSessionRef.current = sid;
    setSessionId(sid);
  }, []);

  const newSession = useCallback(() => {
    const id = `session-${Date.now().toString(36)}`;
    statesRef.current.set(id, emptyState(id));
    activeSessionRef.current = id;
    setSessionId(id);
  }, []);

  const dismissNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const send = useCallback(async (text: string, opts?: {
    sourcePath?: string;
    searchRoot?: string;
    searchQuery?: string;
    saveSummary?: boolean;
    webSearchPermission?: string;
    approvedApprovalId?: string;
    rejectedApprovalId?: string;
    reissueApprovalId?: string;
    notePath?: string;
    uploaded_file?: unknown;
  }) => {
    // Capture the session ID at send time — responses go to THIS session
    const targetSid = sessionId;

    const userMsg: Message = {
      message_id: `tmp-${Date.now()}`,
      role: "user",
      text,
      timestamp: new Date().toISOString(),
    };

    if (!opts?.approvedApprovalId && !opts?.rejectedApprovalId && !opts?.reissueApprovalId) {
      updateState(targetSid, {
        messages: [...getState(targetSid).messages, userMsg],
      });
    }

    const controller = new AbortController();
    updateState(targetSid, {
      isStreaming: true,
      streamingText: "",
      thinkingStatus: "요청 준비 중...",
      abort: controller,
    });

    const payload: Record<string, unknown> = {
      session_id: targetSid,
      user_text: text,
      provider: settings.provider,
      model: settings.model || undefined,
      base_url: settings.baseUrl || undefined,
      search_limit: settings.searchLimit,
      web_search_permission: opts?.webSearchPermission ?? settings.webSearchPermission,
      skip_preflight: settings.skipPreflight || undefined,
    };
    if (settings.notePath) payload.note_path = settings.notePath;
    if (opts?.sourcePath) {
      payload.source_path = opts.sourcePath;
      payload.request_mode = "file";
    }
    if (opts?.uploaded_file) {
      payload.uploaded_file = opts.uploaded_file;
      payload.request_mode = "file";
    }
    if (opts?.searchRoot) {
      payload.search_root = opts.searchRoot;
      payload.search_query = opts.searchQuery ?? text;
      payload.request_mode = "search";
    }
    if (opts?.saveSummary) payload.save_summary = true;
    if (opts?.approvedApprovalId) payload.approved_approval_id = opts.approvedApprovalId;
    if (opts?.rejectedApprovalId) payload.rejected_approval_id = opts.rejectedApprovalId;
    if (opts?.reissueApprovalId) {
      payload.reissue_approval_id = opts.reissueApprovalId;
      if (opts.notePath) payload.note_path = opts.notePath;
    }

    let accumulated = "";

    try {
      for await (const event of streamChat(payload, controller.signal)) {
        if (event.event === "phase") {
          updateState(targetSid, { thinkingStatus: event.title || event.detail || "처리 중..." });
        } else if (event.event === "runtime_status") {
          const reachable = event.reachable;
          const provider = event.provider || "모델";
          updateState(targetSid, {
            thinkingStatus: reachable ? `${provider} 연결 확인됨` : `${provider} 연결 확인 중...`,
          });
        } else if (event.event === "response_origin") {
          const badge = event.badge || event.provider || "";
          updateState(targetSid, {
            thinkingStatus: badge ? `${badge} 응답 생성 중...` : "응답 생성 중...",
          });
        } else if (event.event === "text_delta" && event.text) {
          accumulated += event.text;
          updateState(targetSid, { streamingText: accumulated, thinkingStatus: "응답 작성 중..." });
        } else if (event.event === "text_replace" && event.text) {
          accumulated = event.text;
          updateState(targetSid, { streamingText: accumulated, thinkingStatus: "응답 작성 중..." });
        } else if (event.event === "final" && event.data) {
          const resp = event.data.response;
          const session = event.data.session;
          if (session) {
            const approvals = session.pending_approvals ?? [];
            updateState(targetSid, {
              messages: session.messages,
              title: session.title,
              pendingApproval: approvals.length > 0 ? approvals[approvals.length - 1] : null,
            });
          } else if (resp) {
            const assistantMsg: Message = {
              message_id: resp.message_id ?? `resp-${Date.now()}`,
              role: "assistant",
              text: resp.text,
              timestamp: new Date().toISOString(),
              status: resp.status,
              response_origin: resp.response_origin,
              evidence: resp.evidence,
              summary_chunks: resp.summary_chunks,
              claim_coverage: resp.claim_coverage,
              artifact_id: resp.artifact_id,
              artifact_kind: resp.artifact_kind,
              search_results: resp.search_results,
              applied_preferences: resp.applied_preferences,
            };
            updateState(targetSid, {
              messages: [...getState(targetSid).messages, assistantMsg],
            });
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        const errorMsg: Message = {
          message_id: `err-${Date.now()}`,
          role: "assistant",
          text: `오류가 발생했습니다: ${(err as Error).message}`,
          timestamp: new Date().toISOString(),
          status: "error",
        };
        updateState(targetSid, {
          messages: [...getState(targetSid).messages, errorMsg],
        });
      }
    } finally {
      const wasBackground = activeSessionRef.current !== targetSid;
      updateState(targetSid, {
        isStreaming: false,
        streamingText: "",
        thinkingStatus: "",
        abort: null,
        justCompleted: wasBackground,
      });
      if (wasBackground) {
        const title = getState(targetSid).title || targetSid;
        const nid = `notif-${Date.now()}`;
        setNotifications((prev) => [...prev, { id: nid, title, sid: targetSid }]);
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
          setNotifications((prev) => prev.filter((n) => n.id !== nid));
        }, 5000);
        // Clear justCompleted after 8 seconds
        setTimeout(() => {
          updateState(targetSid, { justCompleted: false });
        }, 8000);
      }
      loadSessions();
    }
  }, [sessionId, settings, loadSessions, getState, updateState]);

  const approve = useCallback((approvalId: string) => {
    send("", { approvedApprovalId: approvalId });
  }, [send]);

  const reject = useCallback((approvalId: string) => {
    send("", { rejectedApprovalId: approvalId });
  }, [send]);

  const cancel = useCallback(() => {
    getState(sessionId).abort?.abort();
  }, [sessionId, getState]);

  const deleteSession = useCallback(async (targetId?: string) => {
    const sid = targetId || sessionId;
    await apiDeleteSession(sid);
    statesRef.current.delete(sid);
    if (sid === sessionId) {
      newSession();
    }
    await loadSessions();
  }, [sessionId, newSession, loadSessions]);

  const deleteAll = useCallback(async () => {
    await apiDeleteAllSessions();
    statesRef.current.clear();
    newSession();
    setSessions([]);
  }, [newSession]);

  // Current session state (for rendering)
  const current = getState(sessionId);

  // Which sessions are streaming / just completed in background?
  const backgroundStreaming = new Set<string>();
  const completedSessions = new Set<string>();
  statesRef.current.forEach((s, sid) => {
    if (sid !== sessionId && s.isStreaming) backgroundStreaming.add(sid);
    if (s.justCompleted) completedSessions.add(sid);
  });

  return {
    sessionId,
    sessionTitle: current.title,
    sessions,
    messages: current.messages,
    pendingApproval: current.pendingApproval,
    streamingText: current.streamingText,
    isStreaming: current.isStreaming,
    thinkingStatus: current.thinkingStatus,
    reviewQueueCount: current.reviewQueueCount,
    backgroundStreaming,
    completedSessions,
    notifications,
    dismissNotification,
    send,
    approve,
    reject,
    cancel,
    switchSession,
    newSession,
    deleteSession,
    deleteAll,
    loadSession,
  };
}
