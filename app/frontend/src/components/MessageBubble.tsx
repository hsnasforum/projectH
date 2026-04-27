import { useState, useRef, useEffect, useMemo, type ReactNode } from "react";
import { marked } from "marked";
import { fetchPreferences, pausePreference, updatePreferenceDescription } from "../api/client";
import type { PreferenceRecord } from "../api/client";
import type { Message } from "../types";
import LinkChip from "./LinkChip";

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,
  gfm: true,
});

const URL_REGEX = /(https?:\/\/[^\s<>"')\]]+)/g;

const CONTENT_REASON_LABELS = [
  { value: "explicit_content_rejection", label: "일반 거절" },
  { value: "fact_error", label: "사실 오류" },
  { value: "tone_error", label: "문체 불만족" },
  { value: "missing_info", label: "누락 정보" },
] as const;

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
  onContentVerdict?: (messageId: string, verdict: string) => void;
  onContentReasonNote?: (messageId: string, note: string) => void;
  onContentReasonLabel?: (messageId: string, label: string) => void;
  onCorrectedSave?: (messageId: string) => void;
}

export default function MessageBubble({
  message,
  onCorrection,
  onFeedback,
  onContentVerdict,
  onContentReasonNote,
  onContentReasonLabel,
  onCorrectedSave,
}: Props) {
  const isUser = message.role === "user";
  const [hovered, setHovered] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const [showDiff, setShowDiff] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showRejectNote, setShowRejectNote] = useState(false);
  const [rejectNote, setRejectNote] = useState("");
  const [rejected, setRejected] = useState(false);
  const [prefPopoverOpen, setPrefPopoverOpen] = useState(false);
  const [fullPreferences, setFullPreferences] = useState<PreferenceRecord[]>([]);
  const [editingPrefId, setEditingPrefId] = useState<string | null>(null);
  const [editDescription, setEditDescription] = useState("");
  const prefBadgeRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [editing]);

  useEffect(() => {
    if (!prefPopoverOpen) return;
    const handler = (event: MouseEvent) => {
      if (prefBadgeRef.current && !prefBadgeRef.current.contains(event.target as Node)) {
        setPrefPopoverOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [prefPopoverOpen]);

  useEffect(() => {
    if (!prefPopoverOpen) return;
    fetchPreferences()
      .then((payload) => {
        setFullPreferences(payload.preferences ?? []);
      })
      .catch(() => {});
  }, [prefPopoverOpen]);

  const isSearchOnly = !isUser
    && (message.search_results?.length ?? 0) > 0
    && message.text.startsWith("검색 결과:");

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

  const pauseAppliedPreference = async (fingerprint: string) => {
    try {
      const preferencesPayload = await fetchPreferences();
      const preferenceId = preferencesPayload.preferences.find(
        (pref) => pref.delta_fingerprint === fingerprint,
      )?.preference_id ?? fingerprint;
      await pausePreference(preferenceId);
    } finally {
      setPrefPopoverOpen(false);
    }
  };

  const savePreferenceDescription = async (preference: PreferenceRecord, description: string) => {
    const trimmed = description.trim();
    if (!trimmed) return;
    const result = await updatePreferenceDescription(preference.preference_id, trimmed);
    setFullPreferences((preferences) => preferences.map((pref) => (
      pref.preference_id === preference.preference_id
        ? { ...pref, ...result.preference, description: result.preference?.description ?? trimmed }
        : pref
    )));
    setEditingPrefId(null);
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
              {isUser ? (
              <div className="whitespace-pre-wrap break-words">{message.text}</div>
            ) : isSearchOnly ? null : (
              <div
                className="prose-sm prose-stone max-w-none break-words
                  [&_a]:text-accent [&_a]:underline [&_a]:underline-offset-2
                  [&_code]:bg-stone-100 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-[13px]
                  [&_pre]:bg-stone-50 [&_pre]:rounded-lg [&_pre]:p-3 [&_pre]:overflow-x-auto [&_pre]:text-[13px]
                  [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5
                  [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mt-3 [&_h1]:mb-1
                  [&_h2]:text-base [&_h2]:font-bold [&_h2]:mt-2 [&_h2]:mb-1
                  [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-2 [&_h3]:mb-1
                  [&_p]:my-1 [&_li]:my-0.5
                  [&_blockquote]:border-l-2 [&_blockquote]:border-stone-300 [&_blockquote]:pl-3 [&_blockquote]:text-muted
                "
                dangerouslySetInnerHTML={{ __html: marked.parse(message.text) as string }}
              />
            )}
              {/* Corrected indicator + diff toggle */}
              {message.corrected_text && (
                <div className="mt-2 pt-2 border-t border-stone-100">
                  <button
                    onClick={() => setShowDiff(!showDiff)}
                    className="text-[11px] text-emerald-600/70 flex items-center gap-1 hover:text-emerald-700 transition-colors"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    교정 완료 {showDiff ? "▲" : "▼"}
                  </button>
                  {showDiff && (
                    <div className="mt-2 space-y-2 text-[12px]">
                      <div className="bg-red-50/50 border border-red-100 rounded-lg px-3 py-2">
                        <span className="text-[10px] font-medium text-red-400 uppercase">원본</span>
                        <p className="mt-1 text-red-700/60 line-through whitespace-pre-wrap">{message.text}</p>
                      </div>
                      <div className="bg-emerald-50/50 border border-emerald-100 rounded-lg px-3 py-2">
                        <span className="text-[10px] font-medium text-emerald-500 uppercase">수정</span>
                        <p className="mt-1 text-emerald-800/70 whitespace-pre-wrap">{message.corrected_text}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
              {!isUser && onCorrectedSave && (
                <div className="mt-1 flex items-center gap-1">
                  <button
                    onClick={() => onCorrectedSave(message.message_id)}
                    disabled={!message.corrected_text}
                    className="text-[11px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title={message.corrected_text ? "수정본을 저장 요청으로 보냅니다" : "수정본을 먼저 기록해 주세요"}
                  >
                    수정본 저장
                  </button>
                </div>
              )}
            </>
          )}

          {/* Action buttons on hover — assistant messages only */}
          {!isUser && !editing && hovered && (
            <div className="absolute -top-3 -right-2 flex items-center gap-1">
              {/* Copy */}
              <button
                onClick={() => {
                  navigator.clipboard.writeText(message.text);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 1500);
                }}
                className="w-7 h-7 rounded-full bg-white border border-stone-200 shadow-sm flex items-center justify-center text-muted/40 hover:text-stone-600 hover:border-stone-300 transition-all"
                title="복사"
              >
                {copied ? (
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2"><path d="M20 6L9 17l-5-5" /></svg>
                ) : (
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></svg>
                )}
              </button>
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
              {/* Content Reject */}
              {onContentVerdict && !rejected && !message.content_verdict && (
                <>
                  <button
                    onClick={() => setShowRejectNote(true)}
                    className="w-7 h-7 rounded-full bg-white border border-stone-200 shadow-sm flex items-center justify-center text-muted/40 hover:text-red-500 hover:border-red-200 transition-all"
                    title="내용 거절"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                  {showRejectNote && (
                    <div className="absolute right-0 top-8 z-10 bg-white border border-stone-200 rounded-lg shadow-md p-2 w-48">
                      <textarea
                        className="w-full text-[11px] resize-none border border-stone-200 rounded p-1 mb-1 focus:outline-none"
                        rows={2}
                        placeholder="거절 이유 (선택)"
                        value={rejectNote}
                        onChange={(e) => setRejectNote(e.target.value)}
                      />
                      <div className="flex gap-1 justify-end">
                        <button
                          className="text-[11px] px-2 py-0.5 rounded bg-stone-100 hover:bg-stone-200"
                          onClick={() => {
                            setShowRejectNote(false);
                            setRejectNote("");
                          }}
                        >
                          취소
                        </button>
                        <button
                          className="text-[11px] px-2 py-0.5 rounded bg-red-100 text-red-600 hover:bg-red-200"
                          onClick={() => {
                            onContentVerdict(message.message_id, "rejected");
                            if (rejectNote.trim() && onContentReasonNote) {
                              onContentReasonNote(message.message_id, rejectNote.trim());
                            }
                            setRejected(true);
                            setShowRejectNote(false);
                            setRejectNote("");
                          }}
                        >
                          거절
                        </button>
                      </div>
                    </div>
                  )}
                </>
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
          {onContentVerdict && (rejected || message.content_verdict === "rejected") && (
            <div className="mt-1 space-y-1">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-50 text-red-500">거절됨</span>
              {onContentReasonLabel && (
                <div className="flex flex-wrap gap-1">
                  {CONTENT_REASON_LABELS.map(({ value, label }) => {
                    const active = (message.content_reason_record?.reason_label ?? "explicit_content_rejection") === value;
                    return (
                      <button
                        key={value}
                        type="button"
                        onClick={() => onContentReasonLabel(message.message_id, value)}
                        className={`text-[10px] px-2 py-0.5 rounded-full border ${
                          active
                            ? "bg-red-100 border-red-300 text-red-600"
                            : "bg-stone-50 border-stone-200 text-stone-400 hover:border-stone-400"
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              )}
              {onContentReasonNote && (
                <div className="flex flex-col gap-1">
                  <textarea
                    className="w-full text-[11px] resize-none border border-stone-200 rounded p-1 focus:outline-none"
                    rows={2}
                    placeholder="거절 이유 (선택)"
                    defaultValue={message.content_reason_record?.reason_note ?? ""}
                    key={message.content_reason_record?.reason_note ?? ""}
                    onBlur={(e) => {
                      const note = e.target.value.trim();
                      if (note) onContentReasonNote(message.message_id, note);
                    }}
                  />
                </div>
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
              <div ref={prefBadgeRef} className="relative inline-flex">
                <button
                  type="button"
                  data-testid="applied-preferences-badge"
                  aria-haspopup="dialog"
                  aria-expanded={prefPopoverOpen}
                  onClick={() => setPrefPopoverOpen((open) => !open)}
                  className="text-[10px] font-medium text-violet-600/70 bg-violet-50 px-2 py-0.5 rounded-full cursor-pointer hover:bg-violet-100 transition-colors"
                  title={message.applied_preferences.map((pref) => pref.description).join("\n")}
                >
                  선호 {message.applied_preferences.length}건 반영
                </button>
                {prefPopoverOpen && (
                  <div
                    data-testid="applied-preferences-popover"
                    className="absolute left-0 top-full mt-1 z-20 w-64 rounded-lg border border-stone-200 bg-white p-2 text-left shadow-lg"
                    onClick={(event) => event.stopPropagation()}
                  >
                    {message.applied_preferences.map((pref) => {
                      const fullPref = fullPreferences.find(
                        (preference) => preference.delta_fingerprint === pref.fingerprint,
                      );
                      const isEditing = editingPrefId === pref.fingerprint;
                      const displayDescription = fullPref?.description ?? pref.description;
                      const hasPreferenceConflict = fullPref?.conflict_info?.has_conflict === true;
                      const isHighQualityPreference = fullPref?.quality_info?.is_high_quality === true;
                      const appliedCount = fullPref?.reliability_stats?.applied_count;
                      const correctedCount = fullPref?.reliability_stats?.corrected_count;
                      const shouldShowReliabilityStats =
                        typeof appliedCount === "number" && Number.isFinite(appliedCount) && appliedCount > 0;
                      const visibleCorrectedCount =
                        typeof correctedCount === "number" && Number.isFinite(correctedCount)
                          ? correctedCount
                          : 0;
                      const isHighSeverityPreferenceConflict =
                        fullPref?.conflict_info?.conflict_severity === "high";
                      const conflictingPreferenceIds =
                        fullPref?.conflict_info?.conflicting_preference_ids ?? [];
                      const preferenceConflictLabel = isHighSeverityPreferenceConflict ? "높은 충돌 위험" : "충돌";
                      const preferenceConflictTitle = conflictingPreferenceIds.length > 0
                        ? `${preferenceConflictLabel}: ${conflictingPreferenceIds.join(", ")}`
                        : preferenceConflictLabel;
                      return (
                        <div
                          key={pref.fingerprint || pref.description}
                          className="flex flex-col gap-1 border-b border-stone-100 px-1 py-1 text-[11px] last:border-0"
                        >
                          <div className="flex items-center justify-between gap-2">
                            {isEditing ? (
                              <input
                                data-testid="pref-description-input"
                                className="flex-1 rounded border border-violet-300 px-1 py-0.5 text-[11px] focus:outline-none"
                                value={editDescription}
                                onChange={(event) => setEditDescription(event.target.value)}
                                autoFocus
                              />
                            ) : (
                              <span className="min-w-0 flex-1 truncate text-stone-700" title={displayDescription}>
                                {displayDescription}
                              </span>
                            )}
                            <div className="flex shrink-0 gap-1">
                              {isEditing ? (
                                <>
                                  <button
                                    type="button"
                                    data-testid="pref-description-save"
                                    onClick={async () => {
                                      if (fullPref) {
                                        await savePreferenceDescription(fullPref, editDescription);
                                      } else {
                                        setEditingPrefId(null);
                                      }
                                    }}
                                    className="rounded border border-violet-200 px-1.5 py-0.5 text-[10px] text-violet-600"
                                  >
                                    저장
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setEditingPrefId(null)}
                                    className="rounded border border-stone-200 px-1.5 py-0.5 text-[10px] text-stone-400"
                                  >
                                    취소
                                  </button>
                                </>
                              ) : (
                                <button
                                  type="button"
                                  data-testid="pref-description-edit"
                                  onClick={() => {
                                    setEditingPrefId(pref.fingerprint);
                                    setEditDescription(displayDescription);
                                  }}
                                  className="rounded border border-stone-200 px-1.5 py-0.5 text-[10px] text-stone-400 hover:text-stone-600"
                                >
                                  편집
                                </button>
                              )}
                              <button
                                type="button"
                                data-testid="preference-pause-btn"
                                onClick={async (event) => {
                                  event.stopPropagation();
                                  await pauseAppliedPreference(pref.fingerprint);
                                }}
                                className="whitespace-nowrap rounded border border-stone-200 px-1.5 py-0.5 text-[10px] text-stone-500 hover:border-stone-300 hover:text-stone-700"
                              >
                                일시중지
                              </button>
                            </div>
                          </div>
                          {isHighQualityPreference && (
                            <span className="w-fit rounded bg-sky-50 px-1 py-0.5 text-[9px] font-medium text-sky-600">
                              고품질
                            </span>
                          )}
                          {hasPreferenceConflict && (
                            <span
                              className={`w-fit rounded border px-1 py-0.5 text-[9px] font-medium ${
                                isHighSeverityPreferenceConflict
                                  ? "border-amber-300 bg-amber-50 text-amber-700"
                                  : "border-orange-200 bg-orange-50 text-orange-700"
                              }`}
                              title={preferenceConflictTitle}
                            >
                              ⚠ 충돌
                            </span>
                          )}
                          {fullPref?.status && fullPref.status !== "active" && (
                            <span className="w-fit rounded bg-stone-100 px-1 py-0.5 text-[9px] font-medium text-stone-500">
                              {fullPref.status === "paused" ? "일시중지" : fullPref.status}
                            </span>
                          )}
                          {fullPref?.last_transition_reason && (
                            <p className="mt-0.5 text-[9px] italic text-stone-400">
                              이유: {fullPref.last_transition_reason}
                            </p>
                          )}
                          {shouldShowReliabilityStats && (
                            <p className="mt-0.5 text-[9px] text-stone-400">
                              적용 {appliedCount}회 · 교정 {visibleCorrectedCount}회
                            </p>
                          )}
                          {fullPref?.original_snippet && (
                            <div className="pl-1 text-[10px] text-stone-400" data-testid="pref-original-snippet">
                              <span className="font-medium">원본: </span>{fullPref.original_snippet}
                            </div>
                          )}
                          {fullPref?.corrected_snippet && (
                            <div className="pl-1 text-[10px] text-violet-500" data-testid="pref-corrected-snippet">
                              <span className="font-medium">교정: </span>{fullPref.corrected_snippet}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
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
              {message.claim_coverage.map((item, i) => {
                const isTrustedWeak = item.status === "weak" && (item.trusted_source_count ?? 0) > 0;
                return (
                  <span
                    key={i}
                    title={item.source_role ? item.source_role.charAt(0).toUpperCase() + item.source_role.slice(1) : undefined}
                    className={`
                      text-[11px] font-medium px-2 py-0.5 rounded-full border
                      ${item.status === "strong"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : isTrustedWeak
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-stone-50 text-stone-500 border-stone-200"
                      }
                    `}
                  >
                    {item.slot}{item.status === "strong" ? " ✓" : isTrustedWeak ? " ?" : " -"}
                  </span>
                );
              })}
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
