import { useState, useEffect, useCallback } from "react";
import type { PreferenceAudit, PreferenceRecord } from "../api/client";
import {
  fetchPreferenceAudit,
  fetchPreferences,
  activatePreference,
  pausePreference,
  rejectPreference,
  updatePreferenceDescription,
} from "../api/client";

const STATUS_LABELS: Record<string, string> = {
  candidate: "후보",
  active: "활성",
  paused: "일시중지",
};

const STATUS_COLORS: Record<string, string> = {
  candidate: "bg-amber-100 text-amber-700",
  active: "bg-emerald-100 text-emerald-700",
  paused: "bg-stone-100 text-stone-500",
};

function preferenceReliabilityCounts(pref: PreferenceRecord) {
  const appliedCount = pref.reliability_stats?.applied_count;
  const correctedCount = pref.reliability_stats?.corrected_count;
  return {
    applied: typeof appliedCount === "number" && Number.isFinite(appliedCount) ? appliedCount : 0,
    corrected: typeof correctedCount === "number" && Number.isFinite(correctedCount) ? correctedCount : 0,
  };
}

export default function PreferencePanel() {
  const [preferences, setPreferences] = useState<PreferenceRecord[]>([]);
  const [audit, setAudit] = useState<PreferenceAudit | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [editDescriptions, setEditDescriptions] = useState<Record<string, string | null>>({});
  const [fadingOut, setFadingOut] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [data, auditData] = await Promise.all([
        fetchPreferences(),
        fetchPreferenceAudit(),
      ]);
      // Filter out rejected items entirely
      const visible = (data.preferences ?? []).filter((p) => p.status !== "rejected");
      setPreferences(visible);
      setAudit(auditData);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAction = useCallback(async (
    pref: PreferenceRecord,
    action: "activate" | "pause" | "reject",
  ) => {
    try {
      if (action === "activate") {
        if (pref.conflict_info?.has_conflict) {
          const confirmed = window.confirm(
            "이 선호는 이미 활성화된 다른 선호와 중복될 수 있습니다. 활성화하시겠습니까?",
          );
          if (!confirmed) return;
        }
        await activatePreference(pref.preference_id);
      } else if (action === "pause") await pausePreference(pref.preference_id);
      else {
        await rejectPreference(pref.preference_id);
        // Fade out then remove
        setFadingOut((prev) => new Set(prev).add(pref.preference_id));
        setTimeout(() => {
          setPreferences((prev) => prev.filter((p) => p.preference_id !== pref.preference_id));
          setFadingOut((prev) => { const next = new Set(prev); next.delete(pref.preference_id); return next; });
        }, 500);
        return;
      }
      await load();
    } catch {
      // silent
    }
  }, [load]);

  const handleDescriptionSave = useCallback(async (id: string) => {
    const draft = editDescriptions[id];
    const description = draft?.trim();
    if (!description) return;
    try {
      await updatePreferenceDescription(id, description);
      setEditDescriptions((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      await load();
    } catch {
      // silent
    }
  }, [editDescriptions, load]);

  // Visible count for header
  const activeCount = preferences.filter((p) => p.status === "active").length;
  const candidateCount = preferences.filter((p) => p.status === "candidate").length;

  if (loading && preferences.length === 0) {
    return (
      <div className="text-[12px] text-sidebar-muted px-2 py-3 text-center">
        불러오는 중...
      </div>
    );
  }

  if (preferences.length === 0) {
    return (
      <div className="text-[11px] text-sidebar-muted/60 px-2 py-2 text-center">
        아직 학습된 선호가 없습니다
      </div>
    );
  }

  return (
    <div>
      {/* Header with toggle + counts */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-1 py-1 text-[11px] text-sidebar-muted hover:text-sidebar-text transition-colors"
      >
        <span className="flex items-center gap-1.5">
          {activeCount > 0 && (
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          )}
          <span>
            {activeCount > 0 ? `${activeCount}개 활성` : ""}
            {activeCount > 0 && candidateCount > 0 ? " · " : ""}
            {candidateCount > 0 ? `${candidateCount}개 후보` : ""}
            {activeCount === 0 && candidateCount === 0 ? `${preferences.length}개 일시중지` : ""}
          </span>
        </span>
        <svg
          width="10" height="10" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2"
          className={`transition-transform ${expanded ? "rotate-180" : ""}`}
        >
          <path d="M18 15l-6-6-6 6" />
        </svg>
      </button>

      {/* Collapsible list with max height */}
      {expanded && (
        <div className="max-h-[200px] overflow-y-auto space-y-1 mt-1 pr-0.5">
          {audit && (
            <div className="px-1 text-[10px] text-sidebar-muted/70">
              활성 {audit.by_status["active"] ?? 0}
              {" · "}후보 {audit.by_status["candidate"] ?? 0}
              {audit.conflict_pair_count > 0 && ` · 충돌 ${audit.conflict_pair_count}쌍`}
            </div>
          )}
          {preferences.map((pref) => {
            const reliability = preferenceReliabilityCounts(pref);
            const isHighQuality = pref.quality_info?.is_high_quality === true;
            const hasEvidenceDetail = Boolean(pref.original_snippet && pref.corrected_snippet);
            const isDetailExpanded = expandedItems.has(pref.preference_id);
            const isDescriptionEditing = editDescriptions[pref.preference_id] !== undefined;
            const descriptionDraft = editDescriptions[pref.preference_id] ?? pref.description;
            return (
              <div
                key={pref.preference_id}
                className={`
                  rounded-lg bg-sidebar-hover/50 px-2.5 py-2 transition-all duration-500
                  ${fadingOut.has(pref.preference_id) ? "opacity-0 scale-95" : "opacity-100"}
                `}
              >
                {/* Status + evidence */}
                <div className="flex items-center gap-1.5 mb-1">
                  <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full ${STATUS_COLORS[pref.status] ?? "bg-stone-100 text-stone-500"}`}>
                    {STATUS_LABELS[pref.status] ?? pref.status}
                  </span>
                  <span className="text-[9px] text-sidebar-muted/60">
                    {pref.cross_session_count}세션 · {pref.evidence_count}건
                  </span>
                  {isHighQuality && (
                    <span className="inline-flex items-center rounded-full bg-sky-500/15 px-1 py-0.5 text-[9px] font-semibold text-sky-300">
                      고품질
                    </span>
                  )}
                  {pref.conflict_info?.has_conflict && (
                    <span
                      data-testid="pref-conflict-badge"
                      className="shrink-0 rounded-full border border-orange-200 bg-orange-50 px-1.5 py-0.5 text-[10px] font-medium text-orange-700"
                      title={`충돌: ${pref.conflict_info.conflicting_preference_ids.join(", ")}`}
                    >
                      ⚠ 충돌
                    </span>
                  )}
                </div>

                {/* Description */}
                {isDescriptionEditing ? (
                  <div className="mb-1.5 space-y-1">
                    <textarea
                      data-testid="pref-description-textarea"
                      className="min-h-[72px] w-full resize-none rounded border border-white/10 bg-sidebar px-2 py-1.5 text-[12px] leading-snug text-sidebar-text outline-none focus:border-sky-300/60"
                      rows={3}
                      value={descriptionDraft}
                      onChange={(event) =>
                        setEditDescriptions((prev) => ({
                          ...prev,
                          [pref.preference_id]: event.target.value,
                        }))
                      }
                    />
                    <div className="flex gap-1.5">
                      <button
                        data-testid="pref-description-save"
                        className="rounded bg-sky-500/15 px-2 py-1 text-[11px] font-medium text-sky-300 transition-colors hover:bg-sky-500/25 disabled:cursor-not-allowed disabled:opacity-40"
                        disabled={!descriptionDraft.trim()}
                        onClick={() => handleDescriptionSave(pref.preference_id)}
                      >
                        저장
                      </button>
                      <button
                        data-testid="pref-description-cancel"
                        className="rounded bg-white/5 px-2 py-1 text-[11px] font-medium text-sidebar-muted transition-colors hover:bg-white/10 hover:text-sidebar-text"
                        onClick={() =>
                          setEditDescriptions((prev) => {
                            const next = { ...prev };
                            delete next[pref.preference_id];
                            return next;
                          })
                        }
                      >
                        취소
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="text-[11px] text-sidebar-text/80 leading-snug mb-1 line-clamp-2">
                    {pref.description}
                  </p>
                )}

                <div className="mb-1 flex items-center justify-between gap-2">
                  <p className="min-w-0 text-[9px] text-sidebar-muted/50 line-clamp-1">
                    적용 {reliability.applied}회 · 교정 {reliability.corrected}회
                  </p>
                  {!isDescriptionEditing && (
                    <button
                      data-testid="pref-edit-description"
                      className="shrink-0 text-[11px] font-medium text-sky-300 transition-colors hover:text-sky-200 hover:underline"
                      onClick={() =>
                        setEditDescriptions((prev) => ({
                          ...prev,
                          [pref.preference_id]: pref.description,
                        }))
                      }
                    >
                      편집
                    </button>
                  )}
                </div>

                {/* Promotion reason (delta summary) */}
                {pref.delta_summary && (
                  <p className="text-[9px] text-sidebar-muted/50 mb-1.5 line-clamp-1">
                    {pref.delta_summary.replacements?.length
                      ? `교정: ${pref.delta_summary.replacements.map(r => `${r.from}→${r.to}`).join(', ')}`
                      : pref.delta_summary.additions?.length
                        ? `추가: ${pref.delta_summary.additions.join(', ')}`
                        : pref.delta_summary.removals?.length
                          ? `제거: ${pref.delta_summary.removals.join(', ')}`
                          : `${pref.cross_session_count}개 세션에서 반복 감지`
                    }
                  </p>
                )}

                {hasEvidenceDetail && (
                  <button
                    data-testid="pref-detail-toggle"
                    className="mb-1.5 text-[11px] font-medium text-sky-300 transition-colors hover:text-sky-200 hover:underline"
                    onClick={() =>
                      setExpandedItems((prev) => {
                        const next = new Set(prev);
                        if (next.has(pref.preference_id)) {
                          next.delete(pref.preference_id);
                        } else {
                          next.add(pref.preference_id);
                        }
                        return next;
                      })
                    }
                  >
                    {isDetailExpanded ? "접기" : "상세 보기"}
                  </button>
                )}
                {hasEvidenceDetail && isDetailExpanded && (
                  <div className="mb-2 space-y-1 text-[11px] leading-snug">
                    <div>
                      <p className="mb-0.5 font-medium text-sidebar-muted">원문</p>
                      <p className="whitespace-pre-wrap break-words rounded bg-red-500/10 p-1.5 text-red-200">
                        {pref.original_snippet}
                      </p>
                    </div>
                    <div>
                      <p className="mb-0.5 font-medium text-sidebar-muted">교정</p>
                      <p className="whitespace-pre-wrap break-words rounded bg-emerald-500/10 p-1.5 text-emerald-200">
                        {pref.corrected_snippet}
                      </p>
                    </div>
                  </div>
                )}

                {/* Compact actions */}
                <div className="flex items-center gap-1">
                  {pref.status === "candidate" && (
                    <>
                      <button
                        onClick={() => handleAction(pref, "activate")}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors"
                      >
                        활성화
                      </button>
                      <button
                        onClick={() => handleAction(pref, "reject")}
                        className="text-[10px] px-1.5 py-0.5 rounded text-sidebar-muted/40 hover:text-red-400 transition-colors"
                      >
                        거부
                      </button>
                    </>
                  )}
                  {pref.status === "active" && (
                    <button
                      onClick={() => handleAction(pref, "pause")}
                      className="text-[10px] px-1.5 py-0.5 rounded text-sidebar-muted/40 hover:text-sidebar-text transition-colors"
                    >
                      일시중지
                    </button>
                  )}
                  {pref.status === "paused" && (
                    <>
                      <button
                        onClick={() => handleAction(pref, "activate")}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors"
                      >
                        재활성
                      </button>
                      <button
                        onClick={() => handleAction(pref, "reject")}
                        className="text-[10px] px-1.5 py-0.5 rounded text-sidebar-muted/40 hover:text-red-400 transition-colors"
                      >
                        거부
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
