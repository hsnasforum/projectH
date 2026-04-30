import { useState, useEffect, useCallback } from "react";
import type { CorrectionDetailRecord, CorrectionListResponse, CorrectionSummary, PreferenceAudit, PreferenceRecord } from "../api/client";
import {
  confirmCorrectionPattern,
  dismissCorrectionPattern,
  promoteCorrectionPattern,
  fetchCorrectionDetail,
  fetchCorrectionList,
  fetchCorrectionSummary,
  fetchPreferenceAudit,
  fetchPreferences,
  activatePreference,
  deletePreference,
  pausePreference,
  rejectPreference,
  postSyncAdoptedToPreferenceCandidates,
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

type PreferenceStatusFilter = "all" | "candidate" | "active" | "paused";
type PreferenceReliabilityTotals = {
  applied: number;
  corrected: number;
};

interface PanelProps {
  lastAppliedFingerprints?: string[];
  autoActivatedPreferenceNotice?: {
    id: string;
    preferenceId: string;
  } | null;
}

function preferenceReliabilityCounts(pref: PreferenceRecord) {
  const appliedCount = pref.reliability_stats?.applied_count;
  const correctedCount = pref.reliability_stats?.corrected_count;
  return {
    applied: typeof appliedCount === "number" && Number.isFinite(appliedCount) ? appliedCount : 0,
    corrected: typeof correctedCount === "number" && Number.isFinite(correctedCount) ? correctedCount : 0,
  };
}

function isActiveHighQualityPreference(pref: PreferenceRecord) {
  return pref.status === "active" && pref.quality_info?.is_high_quality === true;
}

function isActiveHighlyReliablePreference(pref: PreferenceRecord) {
  return pref.status === "active" && pref.is_highly_reliable === true;
}

function isActiveLowReliabilityPreference(pref: PreferenceRecord) {
  const appliedCount = pref.reliability_stats?.applied_count;
  return (
    pref.status === "active" &&
    typeof appliedCount === "number" &&
    Number.isFinite(appliedCount) &&
    appliedCount >= 3 &&
    pref.is_highly_reliable !== true
  );
}

function formatCorrectionReason(correction: CorrectionDetailRecord) {
  const summary = correction.delta_summary;
  if (!summary) return "교정 이유 정보가 없습니다.";
  if (summary.replacements?.length) {
    return `교체: ${summary.replacements.map((item) => `${item.from} -> ${item.to}`).join(", ")}`;
  }
  if (summary.additions?.length) {
    return `추가: ${summary.additions.join(", ")}`;
  }
  if (summary.removals?.length) {
    return `제거: ${summary.removals.join(", ")}`;
  }
  return "교정 이유 정보가 없습니다.";
}

export default function PreferencePanel({
  lastAppliedFingerprints = [],
  autoActivatedPreferenceNotice = null,
}: PanelProps) {
  const [preferences, setPreferences] = useState<PreferenceRecord[]>([]);
  const [audit, setAudit] = useState<PreferenceAudit | null>(null);
  const [correctionSummary, setCorrectionSummary] = useState<CorrectionSummary | null>(null);
  const [correctionList, setCorrectionList] = useState<CorrectionListResponse | null>(null);
  const [correctionQuery, setCorrectionQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [editDescriptions, setEditDescriptions] = useState<Record<string, string | null>>({});
  const [candidatePreferences, setCandidatePreferences] = useState<PreferenceRecord[] | null>(null);
  const [fadingOut, setFadingOut] = useState<Set<string>>(new Set());
  const [syncingAdopted, setSyncingAdopted] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<PreferenceStatusFilter>("all");
  const [reliabilityTotals, setReliabilityTotals] = useState<PreferenceReliabilityTotals>({
    applied: 0,
    corrected: 0,
  });
  const [highQualityActiveCount, setHighQualityActiveCount] = useState(0);
  const [highlyReliableActiveCount, setHighlyReliableActiveCount] = useState(0);
  const [highSeverityConflictCount, setHighSeverityConflictCount] = useState(0);
  const [lowReliabilityActiveCount, setLowReliabilityActiveCount] = useState(0);
  const [lastPromoteResult, setLastPromoteResult] = useState<{
    promoted: number;
    activated: number;
    isHighlyReliable?: boolean;
  } | null>(null);
  const [selectedCorrectionId, setSelectedCorrectionId] = useState<string | null>(null);
  const [selectedCorrectionDetail, setSelectedCorrectionDetail] = useState<CorrectionDetailRecord | null>(null);
  const [correctionDetailMessage, setCorrectionDetailMessage] = useState<string | null>(null);
  const [visibleAutoActivatedNotice, setVisibleAutoActivatedNotice] = useState<{
    id: string;
    preferenceId: string;
  } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [data, auditData, summary, list] = await Promise.all([
        fetchPreferences(),
        fetchPreferenceAudit(),
        fetchCorrectionSummary().catch(() => null),
        fetchCorrectionList(
          correctionQuery ? { query: correctionQuery } : undefined,
        ).catch(() => null),
      ]);
      // Filter out rejected items entirely
      const visible = (data.preferences ?? []).filter((p) => p.status !== "rejected");
      setPreferences(visible);
      setCandidatePreferences(data.candidate_preferences ?? null);
      setReliabilityTotals({
        applied: typeof data.total_applied === "number" && Number.isFinite(data.total_applied)
          ? data.total_applied
          : visible.reduce((total, pref) => {
              if (pref.status !== "active") return total;
              return total + preferenceReliabilityCounts(pref).applied;
            }, 0),
        corrected: typeof data.total_corrected === "number" && Number.isFinite(data.total_corrected)
          ? data.total_corrected
          : visible.reduce((total, pref) => {
              if (pref.status !== "active") return total;
              return total + preferenceReliabilityCounts(pref).corrected;
            }, 0),
      });
      setHighQualityActiveCount(
        typeof data.high_quality_active_count === "number" && Number.isFinite(data.high_quality_active_count)
          ? data.high_quality_active_count
          : visible.filter(isActiveHighQualityPreference).length,
      );
      setHighlyReliableActiveCount(
        typeof data.highly_reliable_active_count === "number" && Number.isFinite(data.highly_reliable_active_count)
          ? data.highly_reliable_active_count
          : visible.filter(isActiveHighlyReliablePreference).length,
      );
      setLowReliabilityActiveCount(
        typeof data.low_reliability_active_count === "number" && Number.isFinite(data.low_reliability_active_count)
          ? data.low_reliability_active_count
          : visible.filter(isActiveLowReliabilityPreference).length,
      );
      setHighSeverityConflictCount(
        typeof data.high_severity_conflict_count === "number" &&
          Number.isFinite(data.high_severity_conflict_count)
          ? data.high_severity_conflict_count
          : visible.filter(
              (pref) =>
                pref.status === "active" &&
                pref.conflict_info?.conflict_severity === "high",
            ).length,
      );
      setAudit(auditData);
      setCorrectionSummary(summary);
      setCorrectionList(list);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [correctionQuery]);

  useEffect(() => { load(); }, []);

  useEffect(() => {
    if (!autoActivatedPreferenceNotice) return;
    setVisibleAutoActivatedNotice(autoActivatedPreferenceNotice);
    setExpanded(true);
    setStatusFilter("active");
    load();
    const timer = window.setTimeout(() => {
      setVisibleAutoActivatedNotice((current) =>
        current?.id === autoActivatedPreferenceNotice.id ? null : current,
      );
    }, 6000);
    return () => window.clearTimeout(timer);
  }, [autoActivatedPreferenceNotice, load]);

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
        const reason = window.prompt("활성화 이유를 입력하세요 (선택사항):", "");
        if (reason === null) return;
        await activatePreference(pref.preference_id, reason || undefined);
      } else if (action === "pause") {
        const reason = window.prompt("일시중지 이유를 입력하세요 (선택사항):", "");
        if (reason === null) return;
        await pausePreference(pref.preference_id, reason || undefined);
      } else {
        const reason = window.prompt("거부 이유를 입력하세요 (선택사항):", "");
        if (reason === null) return;
        await rejectPreference(pref.preference_id, reason || undefined);
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

  const handleDeletePreference = useCallback(async (pref: PreferenceRecord) => {
    try {
      await deletePreference(pref.preference_id);
      setPreferences((prev) => prev.filter((item) => item.preference_id !== pref.preference_id));
      setCandidatePreferences((prev) =>
        prev == null ? prev : prev.filter((item) => item.preference_id !== pref.preference_id),
      );
      setExpandedItems((prev) => {
        const next = new Set(prev);
        next.delete(pref.preference_id);
        return next;
      });
      setEditDescriptions((prev) => {
        const next = { ...prev };
        delete next[pref.preference_id];
        return next;
      });
      await load();
    } catch {
      // silent
    }
  }, [load]);

  const handleSyncAdopted = useCallback(async () => {
    setSyncingAdopted(true);
    setSyncStatus(null);
    try {
      const result = await postSyncAdoptedToPreferenceCandidates();
      const syncedCount = Number.isFinite(result.synced_count) ? result.synced_count : 0;
      setSyncStatus(syncedCount > 0 ? `${syncedCount}개 동기화됨` : "이미 동기화됨");
      await load();
    } catch {
      setSyncStatus("동기화 실패");
    } finally {
      setSyncingAdopted(false);
    }
  }, [load]);

  const handleCorrectionDetail = useCallback(async (correctionId: string) => {
    const cleanId = correctionId.trim();
    if (!cleanId) return;
    setSelectedCorrectionId(cleanId);
    setSelectedCorrectionDetail(null);
    setCorrectionDetailMessage("교정 상세를 불러오는 중...");
    try {
      const detail = await fetchCorrectionDetail(cleanId);
      if (detail.ok && detail.correction) {
        setSelectedCorrectionDetail(detail.correction);
        setCorrectionDetailMessage(null);
        return;
      }
      setCorrectionDetailMessage(detail.error?.message ?? "교정 상세를 불러오지 못했습니다.");
    } catch {
      setCorrectionDetailMessage("교정 상세를 불러오지 못했습니다.");
    }
  }, []);

  // Visible count for header
  const activeCount = preferences.filter((p) => p.status === "active").length;
  const candidateCount = candidatePreferences != null
    ? candidatePreferences.length
    : preferences.filter((p) => p.status === "candidate").length;
  const pausedCount = preferences.filter((p) => p.status === "paused").length;
  const filteredPreferences = statusFilter === "all"
    ? preferences
    : statusFilter === "candidate" && candidatePreferences != null
    ? candidatePreferences
    : preferences.filter((p) => p.status === statusFilter);
  const statusTabs: Array<{ key: PreferenceStatusFilter; label: string; count: number }> = [
    { key: "all", label: "전체", count: preferences.length },
    { key: "candidate", label: "후보", count: candidateCount },
    { key: "active", label: "활성", count: activeCount },
    { key: "paused", label: "일시중지", count: pausedCount },
  ];
  const adoptedCorrectionsCount = audit?.adopted_corrections_count ?? 0;
  const availableToSyncCount = audit?.available_to_sync_count ?? 0;
  const canSyncAdoptedCorrections = availableToSyncCount > 0;
  const appliedSet = new Set(lastAppliedFingerprints);

  if (loading && preferences.length === 0) {
    return (
      <div className="text-[12px] text-sidebar-muted px-2 py-3 text-center">
        불러오는 중...
      </div>
    );
  }

  if (preferences.length === 0 && !canSyncAdoptedCorrections && !visibleAutoActivatedNotice) {
    return (
      <div className="text-[11px] text-sidebar-muted/60 px-2 py-2 text-center">
        아직 학습된 선호가 없습니다
      </div>
    );
  }

  return (
    <div>
      {visibleAutoActivatedNotice && (
        <div
          data-testid="preference-auto-activated-notice"
          className="mx-1 mb-1 rounded-md border border-emerald-400/20 bg-emerald-500/10 px-2 py-1.5 text-[10px] leading-snug text-emerald-100"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium">선호도로 자동 저장됨</span>
            <a
              data-testid="preference-auto-activated-link"
              href={`#pref-card-${visibleAutoActivatedNotice.preferenceId}`}
              className="shrink-0 font-medium text-emerald-200 hover:text-white hover:underline"
              onClick={() => {
                setExpanded(true);
                setStatusFilter("active");
              }}
            >
              선호에서 보기
            </a>
          </div>
        </div>
      )}
      {/* Header with toggle + counts */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-1 py-1 text-[11px] text-sidebar-muted hover:text-sidebar-text transition-colors"
      >
        <span className="flex min-w-0 flex-1 items-center gap-1.5 text-left">
          {activeCount > 0 && (
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
          )}
          <span className="min-w-0 flex-1">
            <span className="block truncate">
              {activeCount > 0 ? `${activeCount}개 활성` : ""}
              {activeCount > 0 && candidateCount > 0 ? " · " : ""}
              {candidateCount > 0 ? `${candidateCount}개 후보` : ""}
              {activeCount === 0 && candidateCount === 0
                ? canSyncAdoptedCorrections
                  ? `활성 교정 ${adoptedCorrectionsCount}개`
                  : `${pausedCount}개 일시중지`
                : ""}
            </span>
            {activeCount > 0 && (
              <span className="block truncate text-[10px] text-sidebar-muted/70">
                총 적용 {reliabilityTotals.applied}회 · 총 교정 {reliabilityTotals.corrected}회
                {highQualityActiveCount > 0 ? ` · 고품질 ${highQualityActiveCount}개` : ""}
                {highlyReliableActiveCount > 0 ? ` · 신뢰도 높음 ${highlyReliableActiveCount}개` : ""}
                {highSeverityConflictCount > 0 && (
                  <span data-testid="high-severity-conflict-count">
                    {` · 충돌 위험 ${highSeverityConflictCount}건`}
                  </span>
                )}
                {lowReliabilityActiveCount > 0 && (
                  <span
                    data-testid="low-reliability-count"
                    className="text-[10px] font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full"
                    title="교정 비율이 높아 현재 응답에 주입되지 않는 활성 선호가 있습니다"
                  >
                    {`신뢰도 저하 ${lowReliabilityActiveCount}건`}
                  </span>
                )}
              </span>
            )}
            {correctionSummary && correctionSummary.total > 0 && (
              <>
                <p
                  data-testid="correction-summary-compact"
                  className="text-[10px] text-sidebar-muted/60 px-2"
                >
                  교정 전체 {correctionSummary.total}개
                  {typeof correctionSummary.by_status["active"] === "number"
                    ? ` · 활성 ${correctionSummary.by_status["active"]}개`
                    : ""}
                </p>
                {correctionSummary.top_recurring_fingerprints[0]?.original_snippet && (
                  <div className="flex items-center gap-1 px-2">
                    <p
                      data-testid="correction-top-pattern"
                      className="text-[10px] text-sidebar-muted/50 truncate flex-1"
                      title={correctionSummary.top_recurring_fingerprints[0].original_snippet}
                    >
                      반복 교정: {correctionSummary.top_recurring_fingerprints[0].original_snippet.slice(0, 40)}
                    </p>
                    <button
                      data-testid="correction-confirm-pattern"
                      className="text-[10px] text-sidebar-muted/70 hover:text-sidebar-foreground shrink-0"
                      onClick={async () => {
                        const fp = correctionSummary.top_recurring_fingerprints[0].delta_fingerprint;
                        await confirmCorrectionPattern(fp).catch(() => null);
                        load();
                      }}
                    >
                      승인
                    </button>
                    <button
                      data-testid="correction-dismiss-pattern"
                      className="text-[10px] text-sidebar-muted/70 hover:text-sidebar-foreground shrink-0"
                      onClick={async () => {
                        const fp = correctionSummary.top_recurring_fingerprints[0].delta_fingerprint;
                        await dismissCorrectionPattern(fp).catch(() => null);
                        load();
                      }}
                    >
                      무시
                    </button>
                    <button
                      data-testid="correction-promote-pattern"
                      className="text-[10px] text-sidebar-muted/70 hover:text-sidebar-foreground shrink-0"
                      onClick={async () => {
                        const fp = correctionSummary.top_recurring_fingerprints[0].delta_fingerprint;
                        const result = await promoteCorrectionPattern(fp).catch(() => null);
                        if (result) {
                          setLastPromoteResult({
                            promoted: result.promoted_count,
                            activated: result.activated_count ?? 0,
                            isHighlyReliable: result.is_highly_reliable ?? false,
                          });
                        }
                        load();
                      }}
                    >
                      승격
                    </button>
                    {lastPromoteResult !== null && (
                      <span
                        data-testid="correction-promote-result"
                        className="text-[9px] text-sidebar-muted/50 ml-1"
                      >
                        {lastPromoteResult.promoted > 0
                          ? `✓ ${lastPromoteResult.activated}개 활성화`
                          : "승격 완료 (활성화 없음)"}
                        {lastPromoteResult.isHighlyReliable && (
                          <span className="ml-1 text-[9px] font-semibold text-emerald-400">
                            · 신뢰도 높음
                          </span>
                        )}
                      </span>
                    )}
                  </div>
                )}
                {correctionList && (
                  <div className="px-2 mt-1">
                    <input
                      type="text"
                      data-testid="correction-search-input"
                      className="w-full text-[10px] bg-transparent border-b border-sidebar-muted/20 text-sidebar-foreground placeholder:text-sidebar-muted/40 px-2 py-0.5 mb-0.5 outline-none"
                      placeholder="교정 검색..."
                      value={correctionQuery}
                      onChange={(e) => setCorrectionQuery(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") load(); }}
                    />
                    <p className="text-[10px] text-sidebar-muted/60 mb-0.5">최근 교정</p>
                    {correctionList.corrections.slice(0, 3).map((c) => (
                      <div
                        key={c.correction_id}
                        data-testid="correction-list-item"
                        role="button"
                        tabIndex={0}
                        aria-pressed={selectedCorrectionId === c.correction_id}
                        className={`cursor-pointer rounded px-1 py-0.5 text-[10px] truncate transition-colors ${
                          selectedCorrectionId === c.correction_id
                            ? "bg-sky-500/15 text-sky-200"
                            : "text-sidebar-muted/50 hover:bg-white/5 hover:text-sidebar-text"
                        }`}
                        title={c.original_text}
                        onClick={(event) => {
                          event.stopPropagation();
                          handleCorrectionDetail(c.correction_id);
                        }}
                        onKeyDown={(event) => {
                          if (event.key !== "Enter" && event.key !== " ") return;
                          event.preventDefault();
                          event.stopPropagation();
                          handleCorrectionDetail(c.correction_id);
                        }}
                      >
                        {c.has_active_preference && (
                          <span
                            data-testid="correction-conflict-badge"
                            className="text-[9px] text-yellow-500 mr-1"
                          >
                            [충돌]
                          </span>
                        )}
                        [{c.status}] {(c.original_text ?? "").slice(0, 35)}
                      </div>
                    ))}
                    {(selectedCorrectionId || correctionDetailMessage || selectedCorrectionDetail) && (
                      <div
                        data-testid="correction-detail-panel"
                        className="mt-1 space-y-1 rounded border border-sidebar-muted/20 bg-sidebar-hover/60 p-2 text-[10px] leading-snug text-sidebar-muted/70"
                        onClick={(event) => event.stopPropagation()}
                      >
                        {correctionDetailMessage ? (
                          <p>{correctionDetailMessage}</p>
                        ) : selectedCorrectionDetail ? (
                          <>
                            <div className="flex items-center justify-between gap-2">
                              <span className="min-w-0 truncate font-medium text-sidebar-text">
                                교정 상세
                              </span>
                              <span className="shrink-0 text-[9px] text-sidebar-muted/60">
                                {selectedCorrectionDetail.status}
                              </span>
                            </div>
                            <div>
                              <p className="mb-0.5 font-medium text-sidebar-muted">원문</p>
                              <p className="whitespace-pre-wrap break-words rounded bg-red-500/10 p-1.5 text-red-200">
                                {selectedCorrectionDetail.original_text || "(내용 없음)"}
                              </p>
                            </div>
                            <div>
                              <p className="mb-0.5 font-medium text-sidebar-muted">교정 결과</p>
                              <p className="whitespace-pre-wrap break-words rounded bg-emerald-500/10 p-1.5 text-emerald-200">
                                {selectedCorrectionDetail.corrected_text || "(내용 없음)"}
                              </p>
                            </div>
                            <div>
                              <p className="mb-0.5 font-medium text-sidebar-muted">교정 이유</p>
                              <p className="whitespace-pre-wrap break-words rounded bg-white/5 p-1.5 text-sidebar-muted">
                                {formatCorrectionReason(selectedCorrectionDetail)}
                              </p>
                            </div>
                          </>
                        ) : null}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </span>
        </span>
        <svg
          width="10" height="10" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2"
          className={`shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`}
        >
          <path d="M18 15l-6-6-6 6" />
        </svg>
      </button>

      {/* Collapsible list with max height */}
      {expanded && (
        <div className="max-h-[200px] overflow-y-auto space-y-1 mt-1 pr-0.5">
          {audit && (
            <div className="space-y-1 px-1 text-[10px] text-sidebar-muted/70">
              <div className="flex items-center gap-1.5">
                <span className="min-w-0 flex-1">
                  활성 {audit.by_status["active"] ?? 0}
                  {" · "}후보 {audit.by_status["candidate"] ?? 0}
                  {audit.conflict_pair_count > 0 && ` · 충돌 ${audit.conflict_pair_count}쌍`}
                  {canSyncAdoptedCorrections && ` · 활성 교정 ${adoptedCorrectionsCount}개`}
                </span>
                {canSyncAdoptedCorrections && (
                  <button
                    data-testid="sync-adopted-btn"
                    className="shrink-0 rounded bg-sky-500/15 px-1.5 py-0.5 text-[10px] font-medium text-sky-300 transition-colors hover:bg-sky-500/25 disabled:cursor-not-allowed disabled:opacity-40"
                    disabled={syncingAdopted || loading}
                    onClick={handleSyncAdopted}
                  >
                    {syncingAdopted ? "동기화 중" : "후보 동기화"}
                  </button>
                )}
              </div>
              {syncStatus && (
                <p data-testid="sync-adopted-status" className="text-[10px] text-sky-300">
                  {syncStatus}
                </p>
              )}
            </div>
          )}
          <div className="flex items-center gap-1 overflow-x-auto px-1 pb-0.5">
            {statusTabs.map((tab) => {
              const selected = statusFilter === tab.key;
              return (
                <button
                  key={tab.key}
                  type="button"
                  data-testid={`preference-status-filter-${tab.key}`}
                  aria-pressed={selected}
                  className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium transition-colors ${
                    selected
                      ? "bg-sky-500/20 text-sky-200"
                      : "bg-white/5 text-sidebar-muted hover:bg-white/10 hover:text-sidebar-text"
                  }`}
                  onClick={() => setStatusFilter(tab.key)}
                >
                  {tab.label} ({tab.count})
                </button>
              );
            })}
          </div>
          {filteredPreferences.length === 0 && (
            <div className="px-2 py-2 text-center text-[11px] text-sidebar-muted/60">
              해당 상태 선호가 없습니다
            </div>
          )}
          {filteredPreferences.map((pref) => {
            const reliability = preferenceReliabilityCounts(pref);
            const isHighQuality = pref.quality_info?.is_high_quality === true;
            const isHighlyReliable = pref.is_highly_reliable === true;
            const isHighSeverityConflict = pref.conflict_info?.conflict_severity === "high";
            const hasEvidenceDetail = Boolean(pref.original_snippet && pref.corrected_snippet);
            const isDetailExpanded = expandedItems.has(pref.preference_id);
            const isDescriptionEditing = editDescriptions[pref.preference_id] !== undefined;
            const descriptionDraft = editDescriptions[pref.preference_id] ?? pref.description;
            const reviewReasonNote = pref.review_reason_note?.trim();
            const sourceSessionTitle = pref.source_session_title?.trim();
            const lastTransitionReason = pref.last_transition_reason?.trim();
            return (
              <div
                key={pref.preference_id}
                id={`pref-card-${pref.preference_id}`}
                className={`
                  rounded-lg bg-sidebar-hover/50 px-2.5 py-2 transition-all duration-500
                  ${fadingOut.has(pref.preference_id) ? "opacity-0 scale-95" : "opacity-100"}
                `}
              >
                {/* Status + evidence */}
                <div className="flex flex-wrap items-center gap-1.5 mb-1">
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
                  {isHighlyReliable && (
                    <span className="inline-flex items-center rounded-full bg-emerald-500/15 px-1 py-0.5 text-[9px] font-semibold text-emerald-300">
                      신뢰도 높음
                    </span>
                  )}
                  {pref.status === "active" && !isHighlyReliable && reliability.applied >= 3 && (
                    <span
                      data-testid="preference-low-reliability-badge"
                      className="inline-flex items-center rounded-full bg-amber-500/15 px-1 py-0.5 text-[9px] font-semibold text-amber-400"
                    >
                      신뢰도 저하
                    </span>
                  )}
                  {pref.status === "active" && appliedSet.has(pref.delta_fingerprint ?? "") && (
                    <span
                      data-testid="preference-last-applied-badge"
                      className="text-[9px] font-medium text-violet-500 bg-violet-50 px-1.5 py-0.5 rounded-full"
                    >
                      이번 응답 반영
                    </span>
                  )}
                  {pref.conflict_info?.has_conflict && (
                    <span
                      data-testid="pref-conflict-badge"
                      className={`shrink-0 rounded-full border px-1.5 py-0.5 text-[10px] font-medium ${
                        isHighSeverityConflict
                          ? "border-amber-300 bg-amber-400/20 text-amber-100"
                          : "border-orange-200 bg-orange-50 text-orange-700"
                      }`}
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

                {(reviewReasonNote || sourceSessionTitle) && (
                  <div
                    data-testid="pref-audit-trace"
                    className="mb-1.5 space-y-0.5 rounded bg-white/5 px-1.5 py-1 text-[10px] leading-snug text-sidebar-muted"
                  >
                    {sourceSessionTitle && (
                      <p className="truncate">
                        <span className="font-medium text-sidebar-muted/80">출처 세션:</span> {sourceSessionTitle}
                      </p>
                    )}
                    {reviewReasonNote && (
                      <p className="line-clamp-2">
                        <span className="font-medium text-sidebar-muted/80">결정 사유:</span> {reviewReasonNote}
                      </p>
                    )}
                  </div>
                )}

                {lastTransitionReason && (
                  <p className="mt-0.5 text-[10px] italic text-sidebar-muted/70">
                    전환 이유: {lastTransitionReason}
                  </p>
                )}

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
                  <button
                    data-testid="delete-preference-btn"
                    aria-label={`선호 삭제: ${pref.description}`}
                    onClick={() => handleDeletePreference(pref)}
                    className="ml-auto text-[10px] px-1.5 py-0.5 rounded text-red-300/70 hover:bg-red-500/10 hover:text-red-200 transition-colors"
                  >
                    삭제
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
