import { useState, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import { useChat } from "./hooks/useChat";
import { postCorrection, postFeedback } from "./api/client";
import { DEFAULT_SETTINGS } from "./types";
import type { AppSettings } from "./types";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const chat = useChat(settings);

  const toggleSidebar = useCallback(() => setSidebarOpen((v) => !v), []);

  const handleCorrection = useCallback(async (messageId: string, correctedText: string) => {
    await postCorrection(chat.sessionId, messageId, correctedText);
    await chat.loadSession(chat.sessionId);
  }, [chat.sessionId, chat.loadSession]);

  const handleFeedback = useCallback(async (messageId: string, label: string) => {
    await postFeedback(chat.sessionId, messageId, label);
    await chat.loadSession(chat.sessionId);
  }, [chat.sessionId, chat.loadSession]);

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
        onSelectSession={chat.switchSession}
        onNewSession={chat.newSession}
        onDeleteSession={chat.deleteSession}
        onDeleteAll={chat.deleteAll}
        onSettingsChange={setSettings}
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
        onToggleSidebar={toggleSidebar}
        sessionTitle={chat.sessionTitle}
        reviewQueueCount={chat.reviewQueueCount}
      />
    </div>
  );
}
