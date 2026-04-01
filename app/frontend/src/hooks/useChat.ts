import { useState, useEffect, useCallback, useRef } from "react";
import type { Message, SessionSummary, PendingApproval } from "../types";
import { fetchSessions, fetchSession, streamChat, postChat } from "../api/client";

const DEFAULT_SESSION = "demo-session";

export function useChat() {
  const [sessionId, setSessionId] = useState(DEFAULT_SESSION);
  const [sessionTitle, setSessionTitle] = useState(DEFAULT_SESSION);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [pendingApproval, setPendingApproval] = useState<PendingApproval | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const loadSessions = useCallback(async () => {
    const list = await fetchSessions();
    setSessions(list);
  }, []);

  const loadSession = useCallback(async (sid: string) => {
    const session = await fetchSession(sid);
    setMessages(session.messages);
    setSessionTitle(session.title);
    const approvals = session.pending_approvals ?? [];
    setPendingApproval(approvals.length > 0 ? approvals[approvals.length - 1] : null);
  }, []);

  useEffect(() => {
    loadSessions();
    loadSession(sessionId);
  }, [sessionId, loadSessions, loadSession]);

  const switchSession = useCallback((sid: string) => {
    setSessionId(sid);
  }, []);

  const newSession = useCallback(() => {
    const id = `session-${Date.now().toString(36)}`;
    setSessionId(id);
    setMessages([]);
    setPendingApproval(null);
    setSessionTitle(id);
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
  }) => {
    const userMsg: Message = {
      message_id: `tmp-${Date.now()}`,
      role: "user",
      text,
      timestamp: new Date().toISOString(),
    };

    if (!opts?.approvedApprovalId && !opts?.rejectedApprovalId && !opts?.reissueApprovalId) {
      setMessages((prev) => [...prev, userMsg]);
    }

    setIsStreaming(true);
    setStreamingText("");
    const controller = new AbortController();
    abortRef.current = controller;

    const payload: Record<string, unknown> = {
      session_id: sessionId,
      user_text: text,
      provider: "mock",
      web_search_permission: opts?.webSearchPermission ?? "disabled",
    };
    if (opts?.sourcePath) {
      payload.source_path = opts.sourcePath;
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
        if (event.event === "text_delta" && event.text) {
          accumulated += event.text;
          setStreamingText(accumulated);
        } else if (event.event === "text_replace" && event.text) {
          accumulated = event.text;
          setStreamingText(accumulated);
        } else if (event.event === "final" && event.data) {
          const resp = event.data.response;
          const session = event.data.session;
          if (session) {
            setMessages(session.messages);
            setSessionTitle(session.title);
            const approvals = session.pending_approvals ?? [];
            setPendingApproval(approvals.length > 0 ? approvals[approvals.length - 1] : null);
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
            };
            setMessages((prev) => [...prev, assistantMsg]);
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
        setMessages((prev) => [...prev, errorMsg]);
      }
    } finally {
      setIsStreaming(false);
      setStreamingText("");
      abortRef.current = null;
      loadSessions();
    }
  }, [sessionId, loadSessions]);

  const approve = useCallback((approvalId: string) => {
    send("", { approvedApprovalId: approvalId });
  }, [send]);

  const reject = useCallback((approvalId: string) => {
    send("", { rejectedApprovalId: approvalId });
  }, [send]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return {
    sessionId,
    sessionTitle,
    sessions,
    messages,
    pendingApproval,
    streamingText,
    isStreaming,
    send,
    approve,
    reject,
    cancel,
    switchSession,
    newSession,
    loadSession,
  };
}
