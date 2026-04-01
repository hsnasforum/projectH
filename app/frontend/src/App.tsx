import { useState, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import { useChat } from "./hooks/useChat";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const chat = useChat();

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
        onSelectSession={chat.switchSession}
        onNewSession={chat.newSession}
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
