import { useState } from "react";
import type { Message } from "../types";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
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
            rounded-2xl px-4 py-3 text-[15px] leading-[1.75]
            ${isUser
              ? "bg-beige-100 text-ink rounded-br-md"
              : "bg-white border border-stone-100 text-ink rounded-bl-md shadow-sm"
            }
          `}
        >
          <div className="whitespace-pre-wrap break-words">{message.text}</div>
        </div>

        {/* Meta info */}
        {!isUser && message.response_origin && (
          <div className="flex items-center gap-2 mt-1.5 px-1">
            {message.response_origin.badge && (
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted/60 bg-stone-100 px-2 py-0.5 rounded-full">
                {message.response_origin.badge}
              </span>
            )}
            {message.source_type_label && (
              <span className="text-[11px] text-muted/50">
                {message.source_type_label}
              </span>
            )}
          </div>
        )}

        {/* Evidence toggle */}
        {!isUser && message.evidence && message.evidence.length > 0 && (
          <div className="mt-2 px-1">
            <button
              onClick={() => setEvidenceOpen(!evidenceOpen)}
              className="
                text-[12px] text-muted hover:text-ink
                flex items-center gap-1 transition-colors
              "
            >
              <svg
                width="12" height="12" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2"
                className={`transition-transform ${evidenceOpen ? "rotate-90" : ""}`}
              >
                <path d="M9 18l6-6-6-6" />
              </svg>
              근거 {message.evidence.length}건
            </button>

            {evidenceOpen && (
              <div className="mt-2 space-y-2">
                {message.evidence.map((item, i) => (
                  <div
                    key={i}
                    className="text-[13px] text-muted bg-beige-50 rounded-xl px-3.5 py-2.5 border border-beige-200/50"
                  >
                    <span className="font-medium text-ink/80 text-[11px] uppercase tracking-wide">
                      {item.label}
                    </span>
                    <p className="mt-1 leading-relaxed">{item.text}</p>
                  </div>
                ))}
              </div>
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
