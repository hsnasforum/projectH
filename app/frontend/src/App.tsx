import { useState, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import Toast from "./components/Toast";
import type { ToastItem } from "./components/Toast";
import { useChat } from "./hooks/useChat";
import {
  postContentReasonLabel,
  postContentReasonNote,
  postContentVerdict,
  postCorrectedSave,
  postCorrection,
  postCandidateReview,
  postFeedback,
} from "./api/client";
import { DEFAULT_SETTINGS } from "./types";
import type { AppSettings } from "./types";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const chat = useChat(settings);

  const toggleSidebar = useCallback(() => setSidebarOpen((v) => !v), []);

  const addToast = useCallback((type: ToastItem["type"], message: string) => {
    const id = `toast-${Date.now()}`;
    setToasts((prev) => [...prev, { id, type, message }]);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const handleCorrection = useCallback(async (messageId: string, correctedText: string) => {
    try {
      await postCorrection(chat.sessionId, messageId, correctedText);
      await chat.loadSession(chat.sessionId);
      addToast("success", "교정이 제출되었습니다.");
    } catch {
      addToast("error", "교정 제출에 실패했습니다.");
    }
  }, [chat.sessionId, chat.loadSession, addToast]);

  const handleFeedback = useCallback(async (messageId: string, label: string) => {
    try {
      await postFeedback(chat.sessionId, messageId, label);
      await chat.loadSession(chat.sessionId);
    } catch {
      addToast("error", "피드백 제출에 실패했습니다.");
    }
  }, [chat.sessionId, chat.loadSession, addToast]);

  const handleContentVerdict = useCallback(async (messageId: string, verdict: string) => {
    try {
      await postContentVerdict(chat.sessionId, messageId, verdict);
      await chat.loadSession(chat.sessionId);
    } catch {
      addToast("error", "내용 거절 제출에 실패했습니다.");
    }
  }, [chat.sessionId, chat.loadSession, addToast]);

  const handleContentReasonNote = useCallback(async (messageId: string, note: string) => {
    try {
      await postContentReasonNote(chat.sessionId, messageId, note);
    } catch {
      addToast("error", "거절 이유 저장에 실패했습니다.");
    }
  }, [chat.sessionId, addToast]);

  const handleContentReasonLabel = useCallback(async (messageId: string, label: string) => {
    try {
      await postContentReasonLabel(chat.sessionId, messageId, label);
      await chat.loadSession(chat.sessionId);
    } catch {
      // Label update is non-critical.
    }
  }, [chat.sessionId, chat.loadSession]);

  const handleCorrectedSave = useCallback(async (messageId: string) => {
    try {
      await postCorrectedSave(chat.sessionId, messageId);
      await chat.loadSession(chat.sessionId);
    } catch {
      addToast("error", "수정본 저장 요청에 실패했습니다.");
    }
  }, [chat.sessionId, chat.loadSession, addToast]);

  const handleCandidateReview = useCallback(async (
    messageId: string,
    candidateId: string,
    candidateUpdatedAt: string,
    action: "accept" | "defer" | "reject",
  ) => {
    try {
      await postCandidateReview(chat.sessionId, messageId, candidateId, candidateUpdatedAt, action);
      await chat.loadSession(chat.sessionId);
    } catch {
      addToast("error", "검토 액션 제출에 실패했습니다.");
    }
  }, [chat.sessionId, chat.loadSession, addToast]);

  return (
    <div className="flex h-screen overflow-hidden bg-warm-50">
      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-30 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      <Sidebar
        open={sidebarOpen}
        sessions={chat.sessions}
        currentSessionId={chat.sessionId}
        backgroundStreaming={chat.backgroundStreaming}
        completedSessions={chat.completedSessions}
        settings={settings}
        reviewQueueItems={chat.reviewQueueItems}
        reviewQueueCount={chat.reviewQueueCount}
        onSelectSession={chat.switchSession}
        onNewSession={chat.newSession}
        onDeleteSession={chat.deleteSession}
        onDeleteAll={chat.deleteAll}
        onSettingsChange={setSettings}
        onCandidateReview={handleCandidateReview}
      />

      {/* Completion toast notifications — top center */}
      {chat.notifications.length > 0 && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2">
          {chat.notifications.map((n) => (
            <div
              key={n.id}
              className="flex items-center gap-3 bg-white border border-stone-200 shadow-lg rounded-xl px-4 py-3 animate-slide-down cursor-pointer"
              onClick={() => { chat.dismissNotification(n.id); chat.switchSession(n.sid); }}
            >
              <span className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="3">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
              </span>
              <div>
                <p className="text-[13px] font-medium text-ink">{n.title}</p>
                <p className="text-[11px] text-muted">응답 완료</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); chat.dismissNotification(n.id); }}
                className="ml-2 text-stone-300 hover:text-stone-500 transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      <ChatArea
        messages={chat.messages}
        streamingText={chat.streamingText}
        isStreaming={chat.isStreaming}
        thinkingStatus={chat.thinkingStatus}
        approval={chat.pendingApproval}
        settings={settings}
        onSettingsChange={setSettings}
        onSend={chat.send}
        onApprove={chat.approve}
        onReject={chat.reject}
        onCancel={chat.cancel}
        onCorrection={handleCorrection}
        onFeedback={handleFeedback}
        onContentVerdict={handleContentVerdict}
        onContentReasonNote={handleContentReasonNote}
        onContentReasonLabel={handleContentReasonLabel}
        onCorrectedSave={handleCorrectedSave}
        onToggleSidebar={toggleSidebar}
        sessionTitle={chat.sessionTitle}
        reviewQueueCount={chat.reviewQueueCount}
        highQualityReviewCount={chat.highQualityReviewCount}
      />

      {/* Error/success toasts — bottom right */}
      <Toast toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
