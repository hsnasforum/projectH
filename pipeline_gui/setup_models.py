from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any


@dataclass
class SetupDiskState:
    paths: dict[str, Path]
    draft_payload: dict[str, object] | None = None
    request_payload: dict[str, object] | None = None
    preview_payload: dict[str, object] | None = None
    apply_payload: dict[str, object] | None = None
    result_payload: dict[str, object] | None = None
    active_payload: dict[str, object] | None = None
    last_applied_payload: dict[str, object] | None = None
    active_exists: bool = False
    request_exists: bool = False
    preview_exists: bool = False
    apply_exists: bool = False
    result_exists: bool = False
    last_applied_exists: bool = False

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


@dataclass
class SetupActionState:
    mode_state: str = "DraftOnly"
    current_setup_id: str = ""
    current_draft_fingerprint: str = ""
    current_preview_fingerprint: str = ""
    current_request_payload: dict[str, object] | None = None
    current_preview_payload: dict[str, object] | None = None
    current_apply_payload: dict[str, object] | None = None
    current_result_payload: dict[str, object] | None = None
    current_support_resolution: dict[str, object] | None = None
    draft_saved: bool = False
    dirty: bool = False
    has_error: bool = False
    has_warning: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)
    restart_required: bool = False
    cleanup_history: list[str] = field(default_factory=list)
    runtime_launch_resolution: dict[str, object] | None = None
    detail_ready: bool = False


@dataclass
class SetupFastSnapshot:
    form_payload: dict[str, object]
    current_draft_fingerprint: str
    draft_saved: bool
    errors: list[str]
    warnings: list[str]
    infos: list[str]
    support_resolution: dict[str, object]
    runtime_resolution: dict[str, object]
    fast_state: str
    state_text: str
    action_pending: bool
    active_matches_current: bool
    current_setup_id_text: str
    current_preview_fingerprint_text: str

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


@dataclass
class SetupDetailSnapshot:
    form_payload: dict[str, object]
    current_draft_fingerprint: str
    draft_saved: bool
    errors: list[str]
    warnings: list[str]
    infos: list[str]
    support_resolution: dict[str, object]
    current_setup_id: str
    current_request_payload: dict[str, object] | None
    current_preview_payload: dict[str, object] | None
    current_preview_fingerprint: str
    current_apply_payload: dict[str, object] | None
    current_result_payload: dict[str, object] | None
    restart_required: bool
    state: str
    display_support_level: str
    display_controls: dict[str, object]
    validation_text: str
    preview_summary_text: str
    restart_notice_text: str
    apply_readiness_text: str

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def updated(self, **kwargs: Any) -> "SetupDetailSnapshot":
        return replace(self, **kwargs)


@dataclass(frozen=True)
class RuntimeLaunchPresentation:
    text: str
    color: str
    launch_allowed: bool


@dataclass(frozen=True)
class SetupStatusPresentation:
    text: str
    color: str
