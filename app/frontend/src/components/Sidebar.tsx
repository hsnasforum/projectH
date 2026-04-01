import type { SessionSummary } from "../types";

interface Props {
  open: boolean;
  sessions: SessionSummary[];
  currentSessionId: string;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
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

export default function Sidebar({ open, sessions, currentSessionId, onSelectSession, onNewSession }: Props) {
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
        <p className="px-2 pt-3 pb-2 text-[11px] uppercase tracking-widest text-sidebar-muted">
          대화 목록
        </p>
        <div className="space-y-0.5">
          {sessions.map((s) => (
            <button
              key={s.session_id}
              onClick={() => onSelectSession(s.session_id)}
              className={`
                w-full text-left px-3 py-2.5 rounded-lg text-[13px]
                transition-colors group
                ${s.session_id === currentSessionId
                  ? "bg-sidebar-hover text-sidebar-text"
                  : "text-sidebar-muted hover:bg-sidebar-hover hover:text-sidebar-text"
                }
              `}
            >
              <div className="truncate font-medium">{s.title}</div>
              <div className="flex items-center gap-2 mt-0.5 text-[11px] opacity-60">
                <span>{timeAgo(s.updated_at)}</span>
                <span>&middot;</span>
                <span>{s.message_count}개 메시지</span>
              </div>
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="px-3 py-6 text-[13px] text-sidebar-muted text-center">
              아직 대화가 없습니다
            </p>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/[0.06]">
        <p className="text-[11px] text-sidebar-muted">
          로컬 퍼스트 문서 비서
        </p>
      </div>
    </nav>
  );
}
