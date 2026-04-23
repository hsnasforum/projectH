import type { PendingApproval } from "../types";

interface Props {
  approval: PendingApproval;
  onApprove: () => void;
  onReject: () => void;
}

function ApprovalButtons({ onApprove, onReject }: { onApprove: () => void; onReject: () => void }) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={onApprove}
        className="
          px-4 py-2 rounded-xl text-[13px] font-medium
          bg-stone-800 text-white
          hover:bg-stone-700 transition-colors
        "
      >
        승인
      </button>
      <button
        onClick={onReject}
        className="
          px-4 py-2 rounded-xl text-[13px] font-medium
          text-stone-500 hover:text-stone-700
          hover:bg-stone-100 transition-colors
        "
      >
        취소
      </button>
    </div>
  );
}

export default function ApprovalCard({ approval, onApprove, onReject }: Props) {
  const isOperatorAction = approval.kind === "operator_action";

  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center shrink-0 mt-0.5">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b45309" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      </div>

      <div className="flex-1 min-w-0 bg-amber-50/50 border border-amber-200/50 rounded-2xl px-5 py-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
            {isOperatorAction ? "작업 승인 필요" : "저장 승인 필요"}
          </span>
        </div>

        {isOperatorAction ? (
          <div className="text-[13px] text-stone-600 mb-3">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-stone-700">
                {approval.action_kind ?? "operator_action"}
              </span>
            </div>
            {approval.target_id && (
              <div className="text-stone-500 truncate mb-1">{approval.target_id}</div>
            )}
            <div className="flex gap-3 mt-2">
              {approval.is_reversible !== undefined && (
                <span className="text-[11px] text-stone-500">
                  {approval.is_reversible ? "되돌리기 가능" : "되돌리기 불가"}
                </span>
              )}
              {approval.audit_trace_required && (
                <span className="text-[11px] text-amber-600">감사 추적 필요</span>
              )}
            </div>
          </div>
        ) : (
          <div className="text-[13px] text-stone-600 mb-3">
            <div className="flex items-center gap-2 mb-1">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="opacity-40">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              </svg>
              <span className="font-medium text-stone-700 truncate">
                {approval.requested_path}
              </span>
            </div>
            {approval.overwrite && (
              <span className="text-[11px] text-amber-600">기존 파일을 덮어씁니다</span>
            )}
          </div>
        )}

        {!isOperatorAction && approval.preview_markdown && (
          <div className="bg-white rounded-xl px-4 py-3 text-[13px] text-stone-600 leading-relaxed mb-4 border border-stone-100 max-h-[120px] overflow-y-auto">
            <pre className="whitespace-pre-wrap font-sans">{approval.preview_markdown}</pre>
          </div>
        )}

        <ApprovalButtons onApprove={onApprove} onReject={onReject} />
      </div>
    </div>
  );
}
