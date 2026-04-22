import { useRef, useEffect } from "react";
import type { Message, PendingApproval, AppSettings } from "../types";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";
import ApprovalCard from "./ApprovalCard";
import TypingIndicator from "./TypingIndicator";

const MODEL_PRESETS = [
  { value: "auto", label: "자동" },
  { value: "qwen2.5:3b", label: "속도" },
  { value: "qwen2.5:7b", label: "균형" },
  { value: "qwen2.5:14b", label: "정확" },
];

interface Props {
  messages: Message[];
  streamingText: string;
  isStreaming: boolean;
  thinkingStatus: string;
  approval: PendingApproval | null;
  settings: AppSettings;
  onSettingsChange: (s: AppSettings) => void;
  onSend: (text: string, opts?: Record<string, unknown>) => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onCancel: () => void;
  onCorrection?: (messageId: string, correctedText: string) => void;
  onFeedback?: (messageId: string, label: string) => void;
  onContentVerdict?: (messageId: string, verdict: string) => void;
  onContentReasonNote?: (messageId: string, note: string) => void;
  onContentReasonLabel?: (messageId: string, label: string) => void;
  onCorrectedSave?: (messageId: string) => void;
  onToggleSidebar: () => void;
  sessionTitle: string;
  reviewQueueCount?: number;
}

export default function ChatArea({
  messages,
  streamingText,
  isStreaming,
  thinkingStatus,
  approval,
  settings,
  onSettingsChange,
  onSend,
  onApprove,
  onReject,
  onCancel,
  onCorrection,
  onFeedback,
  onContentVerdict,
  onContentReasonNote,
  onContentReasonLabel,
  onCorrectedSave,
  onToggleSidebar,
  sessionTitle,
  reviewQueueCount = 0,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, streamingText]);

  return (
    <main className="flex-1 flex flex-col h-screen min-w-0">
      {/* Header */}
      <header className="flex items-center gap-3 px-5 h-[52px] shrink-0 border-b border-stone-100">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-1.5 rounded-lg text-muted hover:bg-stone-100 transition-colors"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>
        <h1 className="text-[15px] font-semibold text-ink truncate">
          {sessionTitle}
        </h1>
        {settings.provider === "ollama" && (
          <select
            value={settings.model}
            onChange={(e) => onSettingsChange({ ...settings, model: e.target.value })}
            className="
              shrink-0 text-[13px] text-muted bg-stone-50 border border-stone-200
              rounded-lg px-2.5 py-1.5 outline-none
              hover:border-stone-300 focus:border-stone-400
              transition-colors cursor-pointer
            "
          >
            {MODEL_PRESETS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        )}
        <div className="flex-1" />
        {reviewQueueCount > 0 && (
          <span className="shrink-0 text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded-full">
            리뷰 {reviewQueueCount}건
          </span>
        )}
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="max-w-[800px] mx-auto px-6 py-8 md:px-10 lg:px-16">
          {messages.length === 0 && !isStreaming && (
            <div className="flex flex-col items-center justify-center pt-24 text-center">
              <div className="w-12 h-12 rounded-full bg-beige-100 flex items-center justify-center mb-5">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#b45309" strokeWidth="1.5">
                  <path d="M12 3v18M3 12h18" strokeLinecap="round" />
                </svg>
              </div>
              <h2 className="text-xl font-serif text-ink mb-2">
                무엇을 도와드릴까요?
              </h2>
              <p className="text-[14px] text-muted max-w-sm leading-relaxed">
                파일 요약, 문서 검색, 또는 자유롭게 질문해 보세요.
                로컬에서 안전하게 처리됩니다.
              </p>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.message_id}
                message={msg}
                onCorrection={onCorrection}
                onFeedback={onFeedback}
                onContentVerdict={onContentVerdict}
                onContentReasonNote={onContentReasonNote}
                onContentReasonLabel={onContentReasonLabel}
                onCorrectedSave={onCorrectedSave}
              />
            ))}

            {isStreaming && streamingText && (
              <MessageBubble
                message={{
                  message_id: "streaming",
                  role: "assistant",
                  text: streamingText,
                }}
              />
            )}

            {isStreaming && !streamingText && <TypingIndicator status={thinkingStatus} />}

            {approval && (
              <ApprovalCard
                approval={approval}
                onApprove={() => onApprove(approval.approval_id)}
                onReject={() => onReject(approval.approval_id)}
              />
            )}
          </div>
        </div>
      </div>

      {/* Input */}
      <InputBar
        onSend={onSend}
        isStreaming={isStreaming}
        onCancel={onCancel}
      />
    </main>
  );
}
