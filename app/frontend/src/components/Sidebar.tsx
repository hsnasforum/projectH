import { useState } from "react";
import type { SessionSummary, AppSettings } from "../types";
import PreferencePanel from "./PreferencePanel";

interface Props {
  open: boolean;
  sessions: SessionSummary[];
  currentSessionId: string;
  settings: AppSettings;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: () => void;
  onDeleteAll: () => void;
  onSettingsChange: (settings: AppSettings) => void;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "방금";
  if (mins < 60) return `${mins}분 전`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
}

export default function Sidebar({
  open,
  sessions,
  currentSessionId,
  settings,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onDeleteAll,
  onSettingsChange,
}: Props) {
  const [settingsOpen, setSettingsOpen] = useState(false);

  const update = (patch: Partial<AppSettings>) =>
    onSettingsChange({ ...settings, ...patch });

  return (
    <nav
      className={`
        fixed inset-y-0 left-0 z-40 w-[280px] flex flex-col
        bg-sidebar text-sidebar-text
        transition-transform duration-200 ease-out
        lg:relative lg:translate-x-0
        ${open ? "translate-x-0" : "-translate-x-full"}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4">
        <span className="text-[15px] font-semibold tracking-tight text-sidebar-text">
          projectH
        </span>
        <button
          onClick={onNewSession}
          className="
            flex items-center gap-1.5 px-3 py-1.5 text-[13px]
            rounded-lg border border-white/10
            text-sidebar-muted hover:text-sidebar-text hover:bg-sidebar-hover
            transition-colors
          "
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          새 채팅
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto px-3 pb-4">
        <div className="flex items-center justify-between px-2 pt-3 pb-2">
          <p className="text-[11px] uppercase tracking-widest text-sidebar-muted">
            대화 목록
          </p>
          {sessions.length > 0 && (
            <button
              onClick={() => { if (confirm("모든 대화를 삭제하시겠습니까?")) onDeleteAll(); }}
              className="text-[10px] text-sidebar-muted/50 hover:text-red-400 transition-colors"
              title="전체 삭제"
            >
              전체 삭제
            </button>
          )}
        </div>
        <div className="space-y-0.5">
          {sessions.map((s) => (
            <div
              key={s.session_id}
              className={`
                flex items-center rounded-lg text-[13px] transition-colors group
                ${s.session_id === currentSessionId
                  ? "bg-sidebar-hover text-sidebar-text"
                  : "text-sidebar-muted hover:bg-sidebar-hover hover:text-sidebar-text"
                }
              `}
            >
              <button
                onClick={() => onSelectSession(s.session_id)}
                className="flex-1 text-left px-3 py-2.5 min-w-0"
              >
                <div className="truncate font-medium">{s.title}</div>
                <div className="flex items-center gap-2 mt-0.5 text-[11px] opacity-60">
                  <span>{timeAgo(s.updated_at)}</span>
                  <span>&middot;</span>
                  <span>{s.message_count}개 메시지</span>
                </div>
              </button>
              {s.session_id === currentSessionId && (
                <button
                  onClick={(e) => { e.stopPropagation(); if (confirm("이 대화를 삭제하시겠습니까?")) onDeleteSession(); }}
                  className="
                    px-2 py-1 mr-1 rounded text-sidebar-muted/30
                    hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100
                  "
                  title="삭제"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  </svg>
                </button>
              )}
            </div>
          ))}
          {sessions.length === 0 && (
            <p className="px-3 py-6 text-[13px] text-sidebar-muted text-center">
              아직 대화가 없습니다
            </p>
          )}
        </div>
      </div>

      {/* Preference Memory */}
      <div className="border-t border-white/[0.06] px-3 py-2">
        <p className="px-2 pb-2 text-[11px] uppercase tracking-widest text-sidebar-muted flex items-center gap-1.5">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
          선호 기억
        </p>
        <PreferencePanel />
      </div>

      {/* Settings */}
      <div className="border-t border-white/[0.06]">
        <button
          onClick={() => setSettingsOpen(!settingsOpen)}
          className="
            w-full flex items-center justify-between px-5 py-3
            text-[13px] text-sidebar-muted hover:text-sidebar-text
            transition-colors
          "
        >
          <span className="flex items-center gap-2">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            설정
          </span>
          <svg
            width="12" height="12" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2"
            className={`transition-transform duration-150 ${settingsOpen ? "rotate-180" : ""}`}
          >
            <path d="M18 15l-6-6-6 6" />
          </svg>
        </button>

        {settingsOpen && (
          <div className="px-4 pb-4 space-y-3">
            {/* Provider */}
            <label className="block">
              <span className="text-[11px] text-sidebar-muted uppercase tracking-wide">프로바이더</span>
              <select
                value={settings.provider}
                onChange={(e) => update({ provider: e.target.value })}
                className="
                  mt-1 w-full bg-sidebar-hover border border-white/10 rounded-lg
                  text-[13px] text-sidebar-text px-3 py-2 outline-none
                  focus:border-white/20 transition-colors
                "
              >
                <option value="mock">mock</option>
                <option value="ollama">ollama</option>
              </select>
            </label>

            {/* Model */}
            <label className="block">
              <span className="text-[11px] text-sidebar-muted uppercase tracking-wide">모델</span>
              <input
                type="text"
                value={settings.model}
                onChange={(e) => update({ model: e.target.value })}
                placeholder="예: llama3.2:latest"
                className="
                  mt-1 w-full bg-sidebar-hover border border-white/10 rounded-lg
                  text-[13px] text-sidebar-text px-3 py-2 outline-none
                  placeholder:text-sidebar-muted/50
                  focus:border-white/20 transition-colors
                "
              />
            </label>

            {/* Base URL */}
            <label className="block">
              <span className="text-[11px] text-sidebar-muted uppercase tracking-wide">Base URL</span>
              <input
                type="text"
                value={settings.baseUrl}
                onChange={(e) => update({ baseUrl: e.target.value })}
                className="
                  mt-1 w-full bg-sidebar-hover border border-white/10 rounded-lg
                  text-[13px] text-sidebar-text px-3 py-2 outline-none
                  focus:border-white/20 transition-colors
                "
              />
            </label>

            {/* Search limit */}
            <label className="block">
              <span className="text-[11px] text-sidebar-muted uppercase tracking-wide">검색 개수 제한</span>
              <input
                type="number"
                min={1}
                value={settings.searchLimit}
                onChange={(e) => update({ searchLimit: parseInt(e.target.value) || 3 })}
                className="
                  mt-1 w-full bg-sidebar-hover border border-white/10 rounded-lg
                  text-[13px] text-sidebar-text px-3 py-2 outline-none
                  focus:border-white/20 transition-colors
                "
              />
            </label>

            {/* Note path */}
            <label className="block">
              <span className="text-[11px] text-sidebar-muted uppercase tracking-wide">저장 경로</span>
              <input
                type="text"
                value={settings.notePath}
                onChange={(e) => update({ notePath: e.target.value })}
                placeholder="비워두면 notes 디렉터리 기본 경로"
                className="
                  mt-1 w-full bg-sidebar-hover border border-white/10 rounded-lg
                  text-[13px] text-sidebar-text px-3 py-2 outline-none
                  placeholder:text-sidebar-muted/50
                  focus:border-white/20 transition-colors
                "
              />
            </label>

            {/* Web search permission */}
            <label className="block">
              <span className="text-[11px] text-sidebar-muted uppercase tracking-wide">웹 검색 권한</span>
              <select
                value={settings.webSearchPermission}
                onChange={(e) => update({ webSearchPermission: e.target.value })}
                className="
                  mt-1 w-full bg-sidebar-hover border border-white/10 rounded-lg
                  text-[13px] text-sidebar-text px-3 py-2 outline-none
                  focus:border-white/20 transition-colors
                "
              >
                <option value="disabled">차단</option>
                <option value="approval">승인 후 허용</option>
                <option value="enabled">허용</option>
              </select>
            </label>

            {/* Skip preflight */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.skipPreflight}
                onChange={(e) => update({ skipPreflight: e.target.checked })}
                className="w-3.5 h-3.5 rounded accent-accent"
              />
              <span className="text-[12px] text-sidebar-muted">런타임 사전 확인 건너뛰기</span>
            </label>
          </div>
        )}
      </div>
    </nav>
  );
}
