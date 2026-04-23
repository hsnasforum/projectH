import { useState, useEffect, useCallback } from "react";
import type { PreferenceRecord } from "../api/client";
import { fetchPreferences, activatePreference, pausePreference, rejectPreference } from "../api/client";

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
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [fadingOut, setFadingOut] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPreferences();
      // Filter out rejected items entirely
      const visible = (data.preferences ?? []).filter((p) => p.status !== "rejected");
      setPreferences(visible);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAction = useCallback(async (id: string, action: "activate" | "pause" | "reject") => {
    try {
      if (action === "activate") await activatePreference(id);
      else if (action === "pause") await pausePreference(id);
      else {
        await rejectPreference(id);
        // Fade out then remove
        setFadingOut((prev) => new Set(prev).add(id));
        setTimeout(() => {
          setPreferences((prev) => prev.filter((p) => p.preference_id !== id));
          setFadingOut((prev) => { const next = new Set(prev); next.delete(id); return next; });
        }, 500);
        return;
      }
      await load();
    } catch {
      // silent
    }
  }, [load]);

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
          {preferences.map((pref) => {
            const reliability = preferenceReliabilityCounts(pref);
            const isHighQuality = pref.quality_info?.is_high_quality === true;
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
                </div>

                {/* Description */}
                <p className="text-[11px] text-sidebar-text/80 leading-snug mb-1 line-clamp-2">
                  {pref.description}
                  {isHighQuality && (
                    <span className="ml-1 inline-flex items-center rounded-full bg-sky-500/15 px-1 py-0.5 text-[9px] font-semibold text-sky-300">
                      고품질
                    </span>
                  )}
                </p>

                <p className="text-[9px] text-sidebar-muted/50 mb-1 line-clamp-1">
                  적용 {reliability.applied}회 · 교정 {reliability.corrected}회
                </p>

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

                {/* Compact actions */}
                <div className="flex items-center gap-1">
                  {pref.status === "candidate" && (
                    <>
                      <button
                        onClick={() => handleAction(pref.preference_id, "activate")}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors"
                      >
                        활성화
                      </button>
                      <button
                        onClick={() => handleAction(pref.preference_id, "reject")}
                        className="text-[10px] px-1.5 py-0.5 rounded text-sidebar-muted/40 hover:text-red-400 transition-colors"
                      >
                        거부
                      </button>
                    </>
                  )}
                  {pref.status === "active" && (
                    <button
                      onClick={() => handleAction(pref.preference_id, "pause")}
                      className="text-[10px] px-1.5 py-0.5 rounded text-sidebar-muted/40 hover:text-sidebar-text transition-colors"
                    >
                      일시중지
                    </button>
                  )}
                  {pref.status === "paused" && (
                    <>
                      <button
                        onClick={() => handleAction(pref.preference_id, "activate")}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors"
                      >
                        재활성
                      </button>
                      <button
                        onClick={() => handleAction(pref.preference_id, "reject")}
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
