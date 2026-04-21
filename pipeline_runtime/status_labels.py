from __future__ import annotations

from .operator_autonomy import (
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    OPERATOR_APPROVAL_COMPLETED_REASON,
)

_OPERATOR_FACING_LABELS_KO = {
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON: "커밋/푸시 자동 정리 중",
    OPERATOR_APPROVAL_COMPLETED_REASON: "승인 작업 완료, 다음 제어 정리 중",
}

_AUTOMATION_SNAPSHOT_FLAG_LABELS_KO = {
    "stale_advisory_pending": "어드바이저리 요청 대기 중",
}


def operator_facing_reason_label(reason: object) -> str:
    return _OPERATOR_FACING_LABELS_KO.get(str(reason or "").strip(), "")


def progress_phase_label(phase: object) -> str:
    return operator_facing_reason_label(phase)


def automation_snapshot_flag_label(flag_name: object) -> str:
    return _AUTOMATION_SNAPSHOT_FLAG_LABELS_KO.get(str(flag_name or "").strip(), "")
