import { useState, useEffect, useCallback } from "react";
import type { PreferenceRecord } from "../api/client";
import { fetchPreferences, activatePreference, pausePreference, rejectPreference } from "../api/client";

const STATUS_LABELS: Record<string, string> = {
  candidate: "후보",
  active: "활성",
  paused: "일시중지",
  rejected: "거부됨",
};

const STATUS_COLORS: Record<string, string> = {
  candidate: "bg-amber-100 text-amber-700",
  active: "bg-emerald-100 text-emerald-700",
  paused: "bg-stone-100 text-stone-500",
  rejected: "bg-red-100 text-red-600",
};

export default function PreferencePanel() {
  const [preferences, setPreferences] = useState<PreferenceRecord[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPreferences();
      setPreferences(data.preferences ?? []);
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
      else await rejectPreference(id);
      await load();
    } catch {
      // silent
    }
  }, [load]);

  if (loading && preferences.length === 0) {
    return (
      <div className="text-[12px] text-sidebar-muted px-2 py-4 text-center">
        불러오는 중...
      </div>
    );
  }

  if (preferences.length === 0) {
    return (
      <div className="text-[12px] text-sidebar-muted px-2 py-4 text-center">
        아직 학습된 선호가 없습니다.
        <br />
        <span className="text-[11px] opacity-60">
          2개 이상 세션에서 같은 교정 패턴이 감지되면 자동으로 후보가 생성됩니다.
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {preferences.map((pref) => (
        <div
          key={pref.preference_id}
          className="rounded-lg bg-sidebar-hover/50 px-3 py-2.5"
        >
          {/* Header: status badge + evidence */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${STATUS_COLORS[pref.status] ?? "bg-stone-100 text-stone-500"}`}>
              {STATUS_LABELS[pref.status] ?? pref.status}
            </span>
            <span className="text-[10px] text-sidebar-muted">
              {pref.cross_session_count}개 세션 · {pref.evidence_count}건
            </span>
          </div>

          {/* Description */}
          <p className="text-[12px] text-sidebar-text leading-relaxed mb-2">
            {pref.description}
          </p>

          {/* Actions */}
          <div className="flex items-center gap-1.5">
            {pref.status === "candidate" && (
              <>
                <button
                  onClick={() => handleAction(pref.preference_id, "activate")}
                  className="text-[11px] px-2 py-1 rounded-md bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors"
                >
                  활성화
                </button>
                <button
                  onClick={() => handleAction(pref.preference_id, "reject")}
                  className="text-[11px] px-2 py-1 rounded-md text-sidebar-muted hover:bg-white/5 transition-colors"
                >
                  거부
                </button>
              </>
            )}
            {pref.status === "active" && (
              <button
                onClick={() => handleAction(pref.preference_id, "pause")}
                className="text-[11px] px-2 py-1 rounded-md text-sidebar-muted hover:bg-white/5 transition-colors"
              >
                일시중지
              </button>
            )}
            {pref.status === "paused" && (
              <>
                <button
                  onClick={() => handleAction(pref.preference_id, "activate")}
                  className="text-[11px] px-2 py-1 rounded-md bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors"
                >
                  재활성화
                </button>
                <button
                  onClick={() => handleAction(pref.preference_id, "reject")}
                  className="text-[11px] px-2 py-1 rounded-md text-sidebar-muted hover:bg-white/5 transition-colors"
                >
                  거부
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
