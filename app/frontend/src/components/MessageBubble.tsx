import { useState, useRef, useEffect, type ReactNode } from "react";
import type { Message } from "../types";
import LinkChip from "./LinkChip";

const URL_REGEX = /(https?:\/\/[^\s<>"')\]]+)/g;

/** Split text into plain segments and LinkChip elements, stripping "링크:" labels. */
function renderTextWithLinks(text: string): ReactNode[] {
  const cleaned = text.replace(
    new RegExp(`링크:\\s*(https?://[^\\s<>"')\\]]+)`, "g"),
    "$1",
  );

  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  const regex = new RegExp(URL_REGEX);

  while ((match = regex.exec(cleaned)) !== null) {
    if (match.index > lastIndex) {
      parts.push(cleaned.slice(lastIndex, match.index));
    }
    const url = match[1];
    parts.push(<LinkChip key={`link-${match.index}`} url={url} />);
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < cleaned.length) {
    parts.push(cleaned.slice(lastIndex));
  }
  return parts;
}

interface Props {
  message: Message;
  onCorrection?: (messageId: string, correctedText: string) => void;
  onFeedback?: (messageId: string, label: string) => void;
}

export default function MessageBubble({ message, onCorrection, onFeedback }: Props) {
  const isUser = message.role === "user";
  const [hovered, setHovered] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [editing]);

  const startEdit = () => {
    setEditText(message.text);
    setEditing(true);
  };

  const submitEdit = () => {
    const trimmed = editText.trim();
    if (trimmed && trimmed !== message.text && onCorrection) {
      onCorrection(message.message_id, trimmed);
    }
    setEditing(false);
  };

  const cancelEdit = () => {
    setEditing(false);
  };

  return (
    <div
      className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-beige-100 flex items-center justify-center shrink-0 mt-0.5">
          <span className="text-[13px] font-semibold text-accent">H</span>
        </div>
      )}

      <div className={`max-w-[85%] min-w-0 ${isUser ? "order-first" : ""}`}>
        {/* Message body */}
        <div
          className={`
            relative rounded-2xl px-4 py-3 text-[15px] leading-[1.75]
            ${isUser
              ? "bg-beige-100 text-ink rounded-br-md"
              : "bg-white border border-stone-100 text-ink rounded-bl-md shadow-sm"
            }
          `}
        >
          {editing ? (
            /* Inline edit mode */
            <div>
              <textarea
                ref={textareaRef}
                value={editText}
                onChange={(e) => {
                  setEditText(e.target.value);
                  e.target.style.height = "auto";
                  e.target.style.height = e.target.scrollHeight + "px";
                }}
                onKeyDown={(e) => {
                  if (e.key === "Escape") cancelEdit();
                  if (e.key === "Enter" && e.ctrlKey) submitEdit();
                }}
                className="
                  w-full resize-none outline-none text-[15px] leading-[1.75]
                  text-ink bg-transparent min-h-[60px]
                "
              />
              <div className="flex items-center gap-2 mt-2 pt-2 border-t border-stone-100">
                <button
                  onClick={submitEdit}
                  className="text-[12px] px-3 py-1 rounded-lg bg-accent text-white hover:bg-accent/90 transition-colors"
                >
                  교정 제출 (Ctrl+Enter)
                </button>
                <button
                  onClick={cancelEdit}
                  className="text-[12px] px-3 py-1 rounded-lg text-muted hover:text-ink transition-colors"
                >
                  취소 (Esc)
                </button>
              </div>
            </div>
          ) : (
            /* Normal display */
            <>
              <div className="whitespace-pre-wrap break-words">
                {isUser ? message.text : renderTextWithLinks(message.text)}
              </div>
              {/* Corrected indicator */}
              {message.corrected_text && (
                <div className="mt-2 pt-2 border-t border-stone-100 text-[11px] text-emerald-600/70 flex items-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                  교정 완료
                </div>
              )}
            </>
          )}

          {/* Action buttons on hover — assistant messages only */}
          {!isUser && !editing && hovered && (
            <div className="absolute -top-3 -right-2 flex items-center gap-1">
              {/* Helpful */}
              {onFeedback && !message.feedback && (
                <button
                  onClick={() => onFeedback(message.message_id, "helpful")}
                  className="w-7 h-7 rounded-full bg-white border border-stone-200 shadow-sm flex items-center justify-center text-muted/40 hover:text-emerald-500 hover:border-emerald-200 transition-all"
                  title="도움이 됨"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
                  </svg>
                </button>
              )}
              {/* Not helpful */}
              {onFeedback && !message.feedback && (
                <button
                  onClick={() => onFeedback(message.message_id, "incorrect")}
                  className="w-7 h-7 rounded-full bg-white border border-stone-200 shadow-sm flex items-center justify-center text-muted/40 hover:text-red-400 hover:border-red-200 transition-all"
                  title="부정확함"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
                  </svg>
                </button>
              )}
              {/* Edit */}
              {onCorrection && (
                <button
                  onClick={startEdit}
                  className="w-7 h-7 rounded-full bg-white border border-stone-200 shadow-sm flex items-center justify-center text-muted/40 hover:text-accent hover:border-accent/30 transition-all"
                  title="수정"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
              )}
              {/* Feedback already given indicator */}
              {message.feedback && (
                <span className={`
                  text-[10px] px-2 py-0.5 rounded-full
                  ${message.feedback === "helpful" ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"}
                `}>
                  {message.feedback === "helpful" ? "도움됨" : "부정확"}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Meta info */}
        {!isUser && (message.response_origin || (message.applied_preferences && message.applied_preferences.length > 0)) && (
          <div className="flex items-center gap-2 mt-1.5 px-1 flex-wrap">
            {message.response_origin?.badge && (
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted/60 bg-stone-100 px-2 py-0.5 rounded-full">
                {message.response_origin.badge}
              </span>
            )}
            {message.source_type_label && (
              <span className="text-[11px] text-muted/50">
                {message.source_type_label}
              </span>
            )}
            {message.applied_preferences && message.applied_preferences.length > 0 && (
              <span
                className="text-[10px] font-medium text-violet-600/70 bg-violet-50 px-2 py-0.5 rounded-full cursor-help"
                title={message.applied_preferences.map(p => p.description).join('\n')}
              >
                선호 {message.applied_preferences.length}건 반영
              </span>
            )}
          </div>
        )}

        {/* Search results */}
        {!isUser && message.search_results && message.search_results.length > 0 && (
          <div className="mt-3 space-y-1.5 px-1">
            {message.search_results.map((result, i) => (
              <div
                key={i}
                className="flex items-start gap-2 text-[13px] text-muted bg-beige-50 rounded-lg px-3 py-2"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5 shrink-0 opacity-40">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
                </svg>
                <div className="min-w-0">
                  <div className="font-medium text-ink/70 truncate">{result.path}</div>
                  {result.snippet && (
                    <div className="text-[12px] text-muted/60 mt-0.5 line-clamp-2">{result.snippet}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Claim coverage */}
        {!isUser && message.claim_coverage && message.claim_coverage.length > 0 && (
          <div className="mt-3 px-1">
            <div className="flex flex-wrap gap-1.5">
              {message.claim_coverage.map((item, i) => (
                <span
                  key={i}
                  className={`
                    text-[11px] font-medium px-2 py-0.5 rounded-full border
                    ${item.status === "strong"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : item.status === "weak"
                        ? "bg-amber-50 text-amber-700 border-amber-200"
                        : "bg-stone-50 text-stone-500 border-stone-200"
                    }
                  `}
                >
                  {item.slot}{item.status === "strong" ? " ✓" : item.status === "weak" ? " ?" : " -"}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <div className="mt-1 px-1 text-[11px] text-muted/40">
            {new Date(message.timestamp).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-stone-200 flex items-center justify-center shrink-0 mt-0.5">
          <span className="text-[13px] font-semibold text-stone-500">나</span>
        </div>
      )}
    </div>
  );
}
