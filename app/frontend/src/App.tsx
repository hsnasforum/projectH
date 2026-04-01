import { useState, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import { useChat } from "./hooks/useChat";
import { DEFAULT_SETTINGS } from "./types";
import type { AppSettings } from "./types";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const chat = useChat(settings);

  const toggleSidebar = useCallback(() => setSidebarOpen((v) => !v), []);

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
        settings={settings}
        onSelectSession={chat.switchSession}
        onNewSession={chat.newSession}
        onSettingsChange={setSettings}
      />

      <ChatArea
        messages={chat.messages}
        streamingText={chat.streamingText}
        isStreaming={chat.isStreaming}
        approval={chat.pendingApproval}
        onSend={chat.send}
        onApprove={chat.approve}
        onReject={chat.reject}
        onCancel={chat.cancel}
        onToggleSidebar={toggleSidebar}
        sessionTitle={chat.sessionTitle}
      />
    </div>
  );
}
