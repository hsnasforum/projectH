import { useState } from "react";
import type { ReviewQueueItem } from "../api/client";

interface Props {
  items: ReviewQueueItem[];
  sessionId: string;
  onReview: (
    messageId: string,
    candidateId: string,
    candidateUpdatedAt: string,
    action: "accept" | "defer" | "reject",
    statement?: string,
    reasonNote?: string,
  ) => void;
}

function candidateUpdatedAt(item: ReviewQueueItem): string {
  const matchingRef = item.supporting_confirmation_refs.find((ref) => (
    typeof ref.candidate_id === "string" &&
    ref.candidate_id === item.candidate_id &&
    typeof ref.candidate_updated_at === "string"
  ));
  if (typeof matchingRef?.candidate_updated_at === "string") {
    return matchingRef.candidate_updated_at;
  }
  return item.updated_at;
}

function summarizeDelta(item: ReviewQueueItem): string | null {
  const deltaSummary = item.delta_summary;
  if (!deltaSummary) return null;
  if (deltaSummary.replacements?.length) {
    return `교정: ${deltaSummary.replacements.map((replacement) => `${replacement.from}→${replacement.to}`).join(", ")}`;
  }
  if (deltaSummary.additions?.length) {
    return `추가: ${deltaSummary.additions.join(", ")}`;
  }
  if (deltaSummary.removals?.length) {
    return `제거: ${deltaSummary.removals.join(", ")}`;
  }
  return null;
}

function contextRoleLabel(role: string): string {
  if (role === "user") return "사용자";
  if (role === "assistant") return "응답";
  return role || "맥락";
}

function contextRoleClass(role: string): string {
  if (role === "user") return "border-sky-400/20 bg-sky-500/10 text-sky-300";
  if (role === "assistant") return "border-white/10 bg-white/5 text-sidebar-muted";
  return "border-violet-400/20 bg-violet-500/10 text-violet-300";
}

function pluralCount(label: string, count: number): string {
  return `${label} ${count}개`;
}

export default function ReviewQueuePanel({ items, sessionId, onReview }: Props) {
  const [editDrafts, setEditDrafts] = useState<Record<string, string | null>>({});
  const [reasonDrafts, setReasonDrafts] = useState<Record<string, string>>({});
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  if (items.length === 0) return null;

  return (
    <div className="border-t border-white/[0.06] px-3 py-2" aria-label={`${sessionId} review queue`}>
      <p className="px-2 pb-2 text-[11px] uppercase tracking-widest text-sidebar-muted">
        검토 대기 ({items.length})
      </p>
      <ul className="max-h-[220px] space-y-1 overflow-y-auto pr-0.5">
        {items.map((item) => {
          const deltaSummaryText = summarizeDelta(item);
          const isEditing = editDrafts[item.candidate_id] !== undefined;
          const statementDraft = editDrafts[item.candidate_id] ?? item.statement;
          const isExpanded = expandedItems.has(item.candidate_id);
          const hasEvidenceDetail = Boolean(item.original_snippet && item.corrected_snippet);
          const contextTurns = (item.context_turns ?? []).filter((turn) => (
            typeof turn.role === "string" &&
            turn.role.trim() &&
            typeof turn.text === "string" &&
            turn.text.trim()
          ));
          const evidenceSummary = item.evidence_summary;
          const sourceSessionTitle = item.source_session_title?.trim();
          const reasonDraft = reasonDrafts[item.candidate_id] ?? "";
          const reasonNote = reasonDraft.trim() || undefined;
          return (
            <li
              key={`${item.source_message_id}:${item.candidate_id}`}
              className="rounded-lg bg-sidebar-hover/50 px-2.5 py-2 text-[12px]"
            >
              <div className="mb-2 flex items-start gap-2">
                {isEditing ? (
                  <textarea
                    data-testid="review-edit-statement"
                    className="min-h-[72px] flex-1 resize-none rounded border border-white/10 bg-sidebar px-2 py-1.5 text-[12px] leading-snug text-sidebar-text outline-none focus:border-sky-300/60"
                    value={statementDraft}
                    onChange={(event) =>
                      setEditDrafts((prev) => ({ ...prev, [item.candidate_id]: event.target.value }))
                    }
                  />
                ) : (
                  <p className="flex-1 text-sidebar-text/85 leading-snug line-clamp-3">
                    {item.statement}
                  </p>
                )}
                {item.quality_info?.is_high_quality && (
                  <span className="shrink-0 rounded-full bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-300">
                    고품질
                  </span>
                )}
                {item.is_global && (
                  <span className="shrink-0 rounded-full border border-violet-400/20 bg-violet-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-violet-300">
                    범용
                  </span>
                )}
              </div>
              {deltaSummaryText && (
                <p className="mb-2 truncate text-[11px] text-sidebar-muted">
                  {deltaSummaryText}
                </p>
              )}
              {sourceSessionTitle && (
                <p data-testid="review-source-session" className="mb-2 truncate text-[11px] text-sidebar-muted">
                  세션: {sourceSessionTitle}
                </p>
              )}
              {evidenceSummary && (
                <div
                  data-testid="review-evidence-summary"
                  className="mb-2 flex flex-wrap gap-1 text-[10px] font-medium text-sidebar-muted"
                >
                  <span className="rounded-full border border-white/10 bg-white/5 px-1.5 py-0.5">
                    {pluralCount("아티팩트", evidenceSummary.artifact_count)}
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/5 px-1.5 py-0.5">
                    {pluralCount("신호", evidenceSummary.signal_count)}
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/5 px-1.5 py-0.5">
                    {pluralCount("확인", evidenceSummary.confirmation_count)}
                  </span>
                  {evidenceSummary.recurring_session_count > 1 && (
                    <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-1.5 py-0.5 text-amber-300">
                      {evidenceSummary.recurring_session_count}개 세션 반복
                    </span>
                  )}
                </div>
              )}
              {contextTurns.length > 0 && (
                <div
                  data-testid="review-context-turns"
                  className="mb-2 space-y-1 border-l border-white/10 pl-2 text-[11px] leading-snug"
                >
                  <p className="font-medium text-sidebar-muted">대화 맥락</p>
                  {contextTurns.map((turn, index) => (
                    <div
                      key={turn.message_id ?? `${item.candidate_id}:context:${index}`}
                      data-testid="review-context-turn"
                      className="flex min-w-0 gap-1.5"
                    >
                      <span
                        className={`mt-0.5 h-fit shrink-0 rounded-full border px-1.5 py-0.5 text-[10px] font-medium ${contextRoleClass(turn.role.trim())}`}
                      >
                        {contextRoleLabel(turn.role.trim())}
                      </span>
                      <p className="min-w-0 flex-1 whitespace-pre-wrap break-words text-sidebar-muted line-clamp-3">
                        {turn.text.trim()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
              {hasEvidenceDetail && (
                <button
                  data-testid="review-detail-toggle"
                  className="mb-2 text-[11px] font-medium text-sky-300 transition-colors hover:text-sky-200 hover:underline"
                  onClick={() =>
                    setExpandedItems((prev) => {
                      const next = new Set(prev);
                      if (next.has(item.candidate_id)) {
                        next.delete(item.candidate_id);
                      } else {
                        next.add(item.candidate_id);
                      }
                      return next;
                    })
                  }
                >
                  {isExpanded ? "접기" : "상세 보기"}
                </button>
              )}
              {hasEvidenceDetail && isExpanded && (
                <div className="mb-2 space-y-1 text-[11px] leading-snug">
                  <div>
                    <p className="mb-0.5 font-medium text-sidebar-muted">원문</p>
                    <p className="whitespace-pre-wrap break-words rounded bg-red-500/10 p-1.5 text-red-200">
                      {item.original_snippet}
                    </p>
                  </div>
                  <div>
                    <p className="mb-0.5 font-medium text-sidebar-muted">교정</p>
                    <p className="whitespace-pre-wrap break-words rounded bg-emerald-500/10 p-1.5 text-emerald-200">
                      {item.corrected_snippet}
                    </p>
                  </div>
                </div>
              )}
              <label className="mb-2 block text-[11px] font-medium text-sidebar-muted">
                사유 (선택)
                <textarea
                  data-testid="review-reason-note"
                  className="mt-1 min-h-[52px] w-full resize-none rounded border border-white/10 bg-sidebar px-2 py-1.5 text-[12px] leading-snug text-sidebar-text outline-none placeholder:text-sidebar-muted/45 focus:border-sky-300/60"
                  value={reasonDraft}
                  placeholder="왜 이 후보를 수락/거절하시나요?"
                  onChange={(event) =>
                    setReasonDrafts((prev) => ({ ...prev, [item.candidate_id]: event.target.value }))
                  }
                />
              </label>
              <div className="flex gap-1.5">
                <button
                  data-testid="review-accept"
                  className="rounded bg-emerald-600/20 px-2 py-1 text-[11px] font-medium text-emerald-300 transition-colors hover:bg-emerald-600/30"
                  onClick={() => {
                    const statement = isEditing ? editDrafts[item.candidate_id] ?? undefined : undefined;
                    onReview(
                      item.source_message_id,
                      item.candidate_id,
                      candidateUpdatedAt(item),
                      "accept",
                      statement,
                      reasonNote,
                    );
                  }}
                >
                  수락
                </button>
                {!isEditing && (
                  <button
                    data-testid="review-edit"
                    className="rounded border border-sky-500/20 bg-sky-500/15 px-2 py-1 text-[11px] font-medium text-sky-300 transition-colors hover:bg-sky-500/25"
                    onClick={() =>
                      setEditDrafts((prev) => ({ ...prev, [item.candidate_id]: item.statement }))
                    }
                  >
                    편집
                  </button>
                )}
                {isEditing && (
                  <button
                    className="rounded bg-white/5 px-2 py-1 text-[11px] font-medium text-sidebar-muted transition-colors hover:bg-white/10 hover:text-sidebar-text"
                    onClick={() =>
                      setEditDrafts((prev) => {
                        const next = { ...prev };
                        delete next[item.candidate_id];
                        return next;
                      })
                    }
                  >
                    취소
                  </button>
                )}
                <button
                  data-testid="review-defer"
                  className="rounded bg-white/5 px-2 py-1 text-[11px] font-medium text-sidebar-muted transition-colors hover:bg-white/10 hover:text-sidebar-text"
                  onClick={() =>
                    onReview(item.source_message_id, item.candidate_id, candidateUpdatedAt(item), "defer")
                  }
                >
                  보류
                </button>
                <button
                  data-testid="review-reject"
                  className="rounded bg-red-500/10 px-2 py-1 text-[11px] font-medium text-red-300 transition-colors hover:bg-red-500/20"
                  onClick={() =>
                    onReview(
                      item.source_message_id,
                      item.candidate_id,
                      candidateUpdatedAt(item),
                      "reject",
                      undefined,
                      reasonNote,
                    )
                  }
                >
                  거절
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
