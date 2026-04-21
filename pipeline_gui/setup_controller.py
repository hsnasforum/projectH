from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from pipeline_runtime.lane_catalog import (
    build_agent_profile_payload,
    default_role_bindings,
    lane_support_rank_map,
    physical_lane_order,
)
from .platform import atomic_write_json_path, path_exists, read_json_path
from .setup_executor import LocalSetupExecutorAdapter
from .setup_models import (
    RuntimeLaunchPresentation,
    SetupActionState,
    SetupDetailSnapshot,
    SetupDiskState,
    SetupFastSnapshot,
    SetupStatusPresentation,
)
from .setup_presenter import format_setup_support_label, support_style_for_level
from .setup_profile import (
    active_profile_fingerprint,
    build_last_applied_record,
    canonical_setup_payload_for_fingerprint,
    cleanup_stale_setup_artifacts,
    display_resolver_messages,
    fingerprint_payload,
    join_display_resolver_messages,
    reconcile_last_applied,
    resolve_active_profile,
    resolve_project_active_profile,
)
from storage.json_store_base import utc_now_iso


class SetupController:
    def __init__(
        self,
        project: Path,
        *,
        executor_adapter=None,
        agent_order: tuple[str, ...] | None = None,
        agent_support_rank: dict[str, int] | None = None,
        default_apply_result_message: str = "설정 적용 결과가 도착했습니다.",
        detail_pending_text: str = "갱신 중...",
    ) -> None:
        self.project = project
        self.executor_adapter = executor_adapter or LocalSetupExecutorAdapter()
        self.agent_order = agent_order or physical_lane_order()
        self.agent_support_rank = agent_support_rank or lane_support_rank_map()
        self.default_apply_result_message = default_apply_result_message
        self.detail_pending_text = detail_pending_text
        self._disk_state_cache: SetupDiskState | None = None
        self._disk_state_last_refresh: float = 0.0
        self._disk_state_ttl_sec: float = 2.0
        self._runtime_launch_resolution: dict[str, object] | None = None
        self._runtime_launch_resolution_last_refresh: float = 0.0
        self._runtime_launch_resolution_ttl_sec: float = 2.0

    def set_project(self, project: Path) -> None:
        if self.project == project:
            return
        self.project = project
        self.invalidate_runtime_caches()

    def set_executor_adapter(self, executor_adapter) -> None:
        self.executor_adapter = executor_adapter

    def paths(self) -> dict[str, Path]:
        pipeline_dir = self.project / ".pipeline"
        config_dir = pipeline_dir / "config"
        setup_dir = pipeline_dir / "setup"
        return {
            "config_dir": config_dir,
            "setup_dir": setup_dir,
            "active": config_dir / "agent_profile.json",
            "draft": config_dir / "agent_profile.draft.json",
            "request": setup_dir / "request.json",
            "preview": setup_dir / "preview.json",
            "apply": setup_dir / "apply.json",
            "result": setup_dir / "result.json",
            "last_applied": setup_dir / "last_applied.json",
        }

    def default_profile(self) -> dict[str, object]:
        payload = build_agent_profile_payload(
            selected_agents=list(self.agent_order),
            role_bindings=default_role_bindings(),
            advisory_enabled=True,
            operator_stop_enabled=True,
            session_arbitration_enabled=True,
            single_agent_mode=False,
            self_verify_allowed=False,
            self_advisory_allowed=False,
        )
        payload["executor_override"] = "auto"
        return payload

    def collect_form_payload(
        self,
        *,
        selected_agents: list[str],
        implement: str | None,
        verify: str | None,
        advisory: str | None,
        advisory_enabled: bool,
        operator_stop_enabled: bool,
        session_arbitration_enabled: bool,
        self_verify_allowed: bool,
        self_advisory_allowed: bool,
        executor_override: str | None,
    ) -> dict[str, object]:
        advisory_value = advisory if advisory_enabled else None
        return {
            "schema_version": 1,
            "selected_agents": list(selected_agents),
            "role_bindings": {
                "implement": implement or None,
                "verify": verify or None,
                "advisory": advisory_value,
            },
            "role_options": {
                "advisory_enabled": advisory_enabled,
                "operator_stop_enabled": operator_stop_enabled,
                "session_arbitration_enabled": session_arbitration_enabled if advisory_enabled else False,
            },
            "mode_flags": {
                "single_agent_mode": len(selected_agents) == 1,
                "self_verify_allowed": self_verify_allowed,
                "self_advisory_allowed": self_advisory_allowed if advisory_enabled else False,
            },
            "executor_override": executor_override or "auto",
        }

    def recommended_executor(
        self,
        selected_agents: list[str],
        role_bindings: dict[str, str | None],
    ) -> str:
        verify = str(role_bindings.get("verify") or "")
        implement = str(role_bindings.get("implement") or "")
        if verify and verify in selected_agents:
            return verify
        if implement and implement in selected_agents:
            return implement
        if not selected_agents:
            return "auto"
        return max(selected_agents, key=lambda name: self.agent_support_rank.get(name, 0))

    def draft_payload(self, form_payload: dict[str, object]) -> dict[str, object]:
        payload = {
            "schema_version": 1,
            "selected_agents": list(form_payload.get("selected_agents", []) or []),
            "role_bindings": dict(form_payload.get("role_bindings", {}) or {}),
            "role_options": dict(form_payload.get("role_options", {}) or {}),
            "mode_flags": dict(form_payload.get("mode_flags", {}) or {}),
            "executor_override": str(form_payload.get("executor_override") or "auto"),
        }
        payload["metadata"] = {
            "draft_saved_at": utc_now_iso(),
            "saved_by": "launcher",
        }
        return payload

    def active_payload(
        self,
        form_payload: dict[str, object],
        *,
        source_setup_id: str,
    ) -> dict[str, object]:
        payload = {
            "schema_version": 1,
            "selected_agents": list(form_payload.get("selected_agents", []) or []),
            "role_bindings": dict(form_payload.get("role_bindings", {}) or {}),
            "role_options": dict(form_payload.get("role_options", {}) or {}),
            "mode_flags": dict(form_payload.get("mode_flags", {}) or {}),
        }
        payload["metadata"] = {
            "saved_at": utc_now_iso(),
            "saved_by": "launcher",
            "source_setup_id": source_setup_id,
        }
        return payload

    def payload_for_fingerprint(self, payload: dict[str, object]) -> dict[str, object]:
        normalized = canonical_setup_payload_for_fingerprint(payload)
        normalized["schema_version"] = int(normalized.get("schema_version") or 1)
        return normalized

    def fingerprint(self, payload: dict[str, object]) -> str:
        return fingerprint_payload(self.payload_for_fingerprint(payload))

    def active_profile_fingerprint(self, payload: dict[str, object]) -> str:
        return active_profile_fingerprint(payload)

    def effective_executor(self, form_payload: dict[str, object]) -> str:
        override = str(form_payload.get("executor_override") or "auto")
        selected = list(form_payload.get("selected_agents", []) or [])
        if override != "auto" and override in selected:
            return override
        return self.recommended_executor(selected, dict(form_payload.get("role_bindings", {}) or {}))

    def preview_fingerprint(
        self,
        form_payload: dict[str, object],
        *,
        setup_id: str,
        draft_fingerprint: str,
    ) -> str:
        preview_basis = {
            "schema_version": 1,
            "setup_id": setup_id,
            "draft_fingerprint": draft_fingerprint,
            "effective_executor": self.effective_executor(form_payload),
            "config": self.payload_for_fingerprint(form_payload),
        }
        return fingerprint_payload(preview_basis)

    @staticmethod
    def preview_matches_current(
        preview_payload: dict[str, object] | None,
        current_setup_id: str,
        current_draft_fingerprint: str,
    ) -> bool:
        if not preview_payload or not current_setup_id or not current_draft_fingerprint:
            return False
        return (
            str(preview_payload.get("setup_id") or "") == current_setup_id
            and str(preview_payload.get("draft_fingerprint") or "") == current_draft_fingerprint
        )

    @staticmethod
    def result_can_promote_active(
        result_payload: dict[str, object] | None,
        apply_payload: dict[str, object] | None,
        preview_payload: dict[str, object] | None,
        current_setup_id: str,
        draft_payload: dict[str, object] | None,
        current_draft_fingerprint: str,
        draft_fingerprint_fn,
    ) -> tuple[bool, str]:
        if not result_payload or not apply_payload or not preview_payload or not current_setup_id:
            return False, "적용 결과에 필요한 setup 기록이 아직 완성되지 않았습니다."
        if str(result_payload.get("status") or "") != "applied":
            return False, "적용 결과가 성공 상태가 아니어서 active 승격을 보류했습니다."
        if str(result_payload.get("setup_id") or "") != current_setup_id:
            return False, "적용 결과의 setup_id가 현재 setup과 달라 active 승격을 보류했습니다."
        if str(apply_payload.get("setup_id") or "") != current_setup_id:
            return False, "적용 요청의 setup_id가 현재 setup과 달라 active 승격을 보류했습니다."
        if str(preview_payload.get("setup_id") or "") != current_setup_id:
            return False, "미리보기 setup_id가 현재 setup과 달라 active 승격을 보류했습니다."
        approved = str(apply_payload.get("approved_preview_fingerprint") or "")
        if not approved:
            return False, "적용 요청에 승인된 preview fingerprint가 없어 active 승격을 보류했습니다."
        if str(result_payload.get("approved_preview_fingerprint") or "") != approved:
            return False, "적용 결과의 approved preview fingerprint가 apply와 달라 active 승격을 보류했습니다."
        if str(preview_payload.get("preview_fingerprint") or "") != approved:
            return False, "현재 preview fingerprint가 apply 승인값과 달라 active 승격을 보류했습니다."
        if not draft_payload:
            return False, "현재 draft 파일이 없어 active 승격을 보류했습니다."
        if not current_draft_fingerprint:
            return False, "현재 draft fingerprint를 확인할 수 없어 active 승격을 보류했습니다."
        if str(preview_payload.get("draft_fingerprint") or "") != current_draft_fingerprint:
            return False, "현재 draft fingerprint와 preview 기준 draft가 달라 active 승격을 보류했습니다."
        if draft_fingerprint_fn(draft_payload) != current_draft_fingerprint:
            return False, "현재 draft 파일이 바뀌어 active 승격을 보류했습니다."
        return True, ""

    def resolve_support(self, form_payload: dict[str, object]) -> dict[str, object]:
        return resolve_active_profile(form_payload)

    def resolve_runtime_active_profile(self) -> dict[str, object]:
        now = time.time()
        if (
            self._runtime_launch_resolution is not None
            and (now - self._runtime_launch_resolution_last_refresh) < self._runtime_launch_resolution_ttl_sec
        ):
            return self._runtime_launch_resolution
        resolved = resolve_project_active_profile(self.project)
        self._runtime_launch_resolution = resolved
        self._runtime_launch_resolution_last_refresh = now
        return resolved

    def runtime_resolution_messages(self, resolved: dict[str, object]) -> list[str]:
        return display_resolver_messages(resolved)

    def runtime_resolution_detail(self, resolved: dict[str, object]) -> str:
        return " / ".join(self.runtime_resolution_messages(resolved))

    def runtime_resolution_feedback_lines(self, resolved: dict[str, object]) -> list[str]:
        detail_lines = self.runtime_resolution_messages(resolved)
        if not detail_lines:
            return []
        status = str(resolved.get("resolution_state") or "")
        prefix = "오류" if status in {"broken", "needs_migration"} else "경고"
        return [f"{prefix}: 현재 runtime {line}" for line in detail_lines]

    @staticmethod
    def runtime_launch_allowed(setup_state: str, resolved: dict[str, object]) -> bool:
        controls = dict(resolved.get("controls") or {})
        return setup_state in ("ready", "ready_warn") and bool(controls.get("launch_allowed"))

    def build_runtime_launch_presentation(
        self,
        setup_state: str,
        resolved: dict[str, object],
    ) -> RuntimeLaunchPresentation:
        support_level = str(resolved.get("support_level") or "blocked")
        detail = self.runtime_resolution_detail(resolved) or join_display_resolver_messages(resolved)
        text = f"실행 프로필: {format_setup_support_label(support_level)}"
        if detail:
            text = f"{text} — {detail}"
        style = support_style_for_level(support_level)
        return RuntimeLaunchPresentation(
            text=text,
            color=str(style["fg"]),
            launch_allowed=self.runtime_launch_allowed(setup_state, resolved),
        )

    def build_setup_state_presentation(
        self,
        setup_state: str,
        detail: str = "",
        resolved: dict[str, object] | None = None,
    ) -> SetupStatusPresentation:
        if setup_state == "ready":
            text = "설정: ● 준비됨"
            color = "#34d399"
        elif setup_state == "ready_warn":
            text = f"설정: ● 준비됨 ({detail})"
            color = "#f59e0b"
        elif setup_state == "checking":
            text = f"설정: … {detail or '점검 중'}"
            color = "#f59e0b"
        elif setup_state == "missing":
            text = f"설정: ■ 누락 {detail}"
            color = "#ef4444"
        elif setup_state == "failed":
            text = f"설정: ■ {detail or '설치 실패'}"
            color = "#ef4444"
        else:
            text = "설정: — 알 수 없음"
            color = "#888888"

        if setup_state not in {"ready", "ready_warn"} or not resolved:
            return SetupStatusPresentation(text=text, color=color)

        launch = self.build_runtime_launch_presentation(setup_state, resolved)
        support_level = str(resolved.get("support_level") or "")
        runtime_detail = self.runtime_resolution_detail(resolved) or join_display_resolver_messages(resolved)
        if not launch.launch_allowed:
            suffix = "실행 차단"
            if runtime_detail:
                suffix = f"{suffix}: {runtime_detail}"
            return SetupStatusPresentation(text=f"{text} / {suffix}", color="#ef4444")
        if support_level == "experimental":
            suffix = "실험적"
            if runtime_detail:
                suffix = f"{suffix}: {runtime_detail}"
            return SetupStatusPresentation(text=f"{text} / {suffix}", color="#f59e0b")
        return SetupStatusPresentation(text=text, color=color)

    @staticmethod
    def support_banner_lines(
        support_level: str,
        controls: dict[str, object],
    ) -> list[str]:
        if not bool(controls.get("banner_required")):
            return []
        if support_level == "experimental":
            return ["안내: 현재 조합은 실험적 프로필입니다. 수동 확인이 더 필요할 수 있습니다."]
        if support_level == "blocked":
            return ["경고: 현재 프로필은 차단 상태입니다. 미리보기만 허용되고 적용과 launch는 차단됩니다."]
        return []

    def validate(self, form_payload: dict[str, object]) -> tuple[list[str], list[str], list[str]]:
        selected = list(form_payload.get("selected_agents", []) or [])
        bindings = dict(form_payload.get("role_bindings", {}) or {})
        options = dict(form_payload.get("role_options", {}) or {})
        flags = dict(form_payload.get("mode_flags", {}) or {})

        implement = str(bindings.get("implement") or "")
        verify = str(bindings.get("verify") or "")
        advisory = str(bindings.get("advisory") or "")
        advisory_enabled = bool(options.get("advisory_enabled"))
        session_arbitration_enabled = bool(options.get("session_arbitration_enabled"))
        self_verify_allowed = bool(flags.get("self_verify_allowed"))
        self_advisory_allowed = bool(flags.get("self_advisory_allowed"))
        executor_override = str(form_payload.get("executor_override") or "auto")

        errors: list[str] = []
        warnings: list[str] = []
        infos: list[str] = []

        if not selected:
            errors.append("최소 1개의 agent를 선택해야 합니다.")
        if not implement:
            errors.append("구현 역할은 반드시 지정해야 합니다.")
        elif implement not in selected:
            errors.append("구현 역할이 선택되지 않은 agent를 가리킵니다.")

        if verify and verify not in selected:
            errors.append("검증 역할이 선택되지 않은 agent를 가리킵니다.")
        if advisory_enabled and advisory and advisory not in selected:
            errors.append("자문 역할이 선택되지 않은 agent를 가리킵니다.")
        if implement and verify and implement == verify and not self_verify_allowed:
            errors.append("현재 설정에서는 구현 역할과 검증 역할을 같은 agent에 둘 수 없습니다.")
        if advisory_enabled and advisory and not self_advisory_allowed and advisory in {implement, verify}:
            errors.append("현재 설정에서는 자문 역할을 구현/검증과 같은 agent에 둘 수 없습니다.")

        if not verify:
            warnings.append("검증 역할이 비어 있습니다. 자체 검증 또는 수동 확인이 필요할 수 있습니다.")
        if session_arbitration_enabled and not advisory_enabled:
            warnings.append("세션 중재는 자문 역할이 비활성일 때 사용할 수 없습니다.")

        effective_executor = self.effective_executor(form_payload)
        if executor_override == "auto" and effective_executor != "auto":
            infos.append(f"설정 실행자는 {effective_executor}로 자동 선택됩니다.")
        if not advisory_enabled:
            infos.append("자문 역할이 비활성화되어 관련 바인딩과 중재 옵션은 무시됩니다.")
        infos.append("적용 전까지 runtime은 active config만 사용합니다.")
        return errors, warnings, infos

    def write_json(self, path: Path, payload: dict[str, object]) -> None:
        atomic_write_json_path(path, payload)
        self.invalidate_runtime_caches()

    def invalidate_runtime_caches(self) -> None:
        self._disk_state_cache = None
        self._disk_state_last_refresh = 0.0
        self._runtime_launch_resolution = None
        self._runtime_launch_resolution_last_refresh = 0.0

    def read_disk_state(self, *, force: bool = False) -> SetupDiskState:
        now = time.time()
        cached = self._disk_state_cache
        if not force and cached is not None and (now - self._disk_state_last_refresh) < self._disk_state_ttl_sec:
            cached_has_truth = any(
                getattr(cached, flag)
                for flag in (
                    "active_exists",
                    "request_exists",
                    "preview_exists",
                    "apply_exists",
                    "result_exists",
                    "last_applied_exists",
                )
            )
            if not cached_has_truth:
                return cached
            existence_flags = (
                ("active_exists", "active"),
                ("request_exists", "request"),
                ("preview_exists", "preview"),
                ("apply_exists", "apply"),
                ("result_exists", "result"),
                ("last_applied_exists", "last_applied"),
            )
            exists_state_changed = any(
                bool(getattr(cached, flag)) != path_exists(cached.paths[key])
                for flag, key in existence_flags
            )
            if not exists_state_changed:
                return cached

        paths = self.paths()
        state = SetupDiskState(
            paths=paths,
            draft_payload=read_json_path(paths["draft"]),
            request_payload=read_json_path(paths["request"]),
            preview_payload=read_json_path(paths["preview"]),
            apply_payload=read_json_path(paths["apply"]),
            result_payload=read_json_path(paths["result"]),
            active_payload=read_json_path(paths["active"]),
            last_applied_payload=read_json_path(paths["last_applied"]),
            active_exists=path_exists(paths["active"]),
            request_exists=path_exists(paths["request"]),
            preview_exists=path_exists(paths["preview"]),
            apply_exists=path_exists(paths["apply"]),
            result_exists=path_exists(paths["result"]),
            last_applied_exists=path_exists(paths["last_applied"]),
        )
        self._disk_state_cache = state
        self._disk_state_last_refresh = now
        return state

    def record_cleanup_result(
        self,
        state: SetupActionState,
        *,
        source_label: str,
        removed_count: int,
        include_noop: bool = False,
    ) -> str | None:
        if removed_count <= 0 and not include_noop:
            return None
        line = (
            f"{source_label}: 오래된 setup 파일 {removed_count}개 정리"
            if removed_count > 0
            else f"{source_label}: 정리할 오래된 setup 파일이 없습니다"
        )
        history = list(state.cleanup_history)
        history.insert(0, line)
        state.cleanup_history = history[:5]
        return "\n".join(state.cleanup_history)

    def cleanup_staged_files_once_on_startup(self, state: SetupActionState) -> int:
        disk_state = self.read_disk_state(force=True)
        removed = self.cleanup_staged_files(
            state,
            request_payload=disk_state.request_payload,
            preview_payload=disk_state.preview_payload,
            apply_payload=disk_state.apply_payload,
            result_payload=disk_state.result_payload,
            last_applied_payload=disk_state.last_applied_payload,
        )
        self.record_cleanup_result(state, source_label="초기 정리", removed_count=len(removed))
        return len(removed)

    def run_automatic_cleanup(self, state: SetupActionState) -> int:
        disk_state = self.read_disk_state(force=True)
        removed = self.cleanup_staged_files(
            state,
            request_payload=disk_state.request_payload,
            preview_payload=disk_state.preview_payload,
            apply_payload=disk_state.apply_payload,
            result_payload=disk_state.result_payload,
            last_applied_payload=disk_state.last_applied_payload,
        )
        self.record_cleanup_result(state, source_label="자동 정리", removed_count=len(removed))
        return len(removed)

    def protected_staged_setup_ids(
        self,
        state: SetupActionState,
        *,
        request_payload: dict[str, object] | None = None,
        preview_payload: dict[str, object] | None = None,
        apply_payload: dict[str, object] | None = None,
        result_payload: dict[str, object] | None = None,
        last_applied_payload: dict[str, object] | None = None,
        extra_setup_ids: tuple[str, ...] = (),
    ) -> set[str]:
        protected: set[str] = {item for item in extra_setup_ids if item}
        payloads = (
            request_payload,
            apply_payload,
            last_applied_payload,
            state.current_request_payload,
            state.current_apply_payload,
        )
        current_only_payloads = (
            preview_payload,
            result_payload,
            state.current_preview_payload,
            state.current_result_payload,
        )
        if state.mode_state in {"PreviewWaiting", "ApplyPending"} and state.current_setup_id:
            protected.add(state.current_setup_id)
        for payload in payloads:
            if not payload:
                continue
            setup_id = str(payload.get("setup_id") or "").strip()
            if setup_id:
                protected.add(setup_id)
        for payload in current_only_payloads:
            if not payload:
                continue
            setup_id = str(payload.get("setup_id") or "").strip()
            if setup_id and setup_id == state.current_setup_id:
                protected.add(setup_id)
        return {item for item in protected if item}

    def cleanup_staged_files(
        self,
        state: SetupActionState,
        *,
        request_payload: dict[str, object] | None,
        preview_payload: dict[str, object] | None,
        apply_payload: dict[str, object] | None,
        result_payload: dict[str, object] | None,
        last_applied_payload: dict[str, object] | None = None,
    ) -> list[Path]:
        paths = self.paths()
        protected_setup_ids = self.protected_staged_setup_ids(
            state,
            request_payload=request_payload,
            preview_payload=preview_payload,
            apply_payload=apply_payload,
            result_payload=result_payload,
            last_applied_payload=last_applied_payload,
        )
        removed = cleanup_stale_setup_artifacts(
            setup_dir=paths["setup_dir"],
            protected_setup_ids=protected_setup_ids,
        )
        removed.extend(
            self.executor_adapter.cleanup_staged_files(
                setup_dir=paths["setup_dir"],
                protected_setup_ids=protected_setup_ids,
            )
        )
        if removed:
            self.invalidate_runtime_caches()
        return removed

    def summary_text(
        self,
        form_payload: dict[str, object],
        preview_payload: dict[str, object] | None,
        *,
        preview_current: bool,
        stale_preview: bool,
    ) -> str:
        bindings = dict(form_payload.get("role_bindings", {}) or {})
        options = dict(form_payload.get("role_options", {}) or {})
        lines = [
            f"에이전트: {', '.join(form_payload.get('selected_agents', []) or ['—'])}",
            f"구현: {bindings.get('implement') or '—'}",
            f"검증: {bindings.get('verify') or '—'}",
            f"자문: {bindings.get('advisory') or '—'}",
            (
                "옵션: "
                f"자문={'켜짐' if options.get('advisory_enabled') else '꺼짐'} · "
                f"operator 중지={'켜짐' if options.get('operator_stop_enabled') else '꺼짐'} · "
                f"세션 중재={'켜짐' if options.get('session_arbitration_enabled') else '꺼짐'}"
            ),
            f"실행자: {self.effective_executor(form_payload)}",
        ]
        if preview_current and preview_payload:
            support_level = str(preview_payload.get("support_level") or "experimental")
            lines.append("지원 수준: " + format_setup_support_label(support_level))
            planned = preview_payload.get("planned_changes") or {}
            writes = list((planned.get("write") if isinstance(planned, dict) else []) or [])
            if writes:
                lines.append("예정 쓰기: " + ", ".join(str(item) for item in writes[:4]))
            diff_summary = list(preview_payload.get("diff_summary") or [])
            if diff_summary:
                lines.append("미리보기: " + str(diff_summary[0]))
        elif stale_preview and preview_payload:
            lines.append("미리보기: 현재 초안과 맞지 않는 이전 미리보기를 무시했습니다")
        else:
            lines.append("미리보기: 생성된 미리보기가 없습니다")
        return "\n".join(lines)

    def restart_required_for_payload(self, payload: dict[str, object]) -> bool:
        active_payload = read_json_path(self.paths()["active"])
        if not active_payload:
            return True
        return self.active_profile_fingerprint(active_payload) != self.active_profile_fingerprint(payload)

    def active_matches_current_form(
        self,
        active_payload: dict[str, object] | None,
        form_payload: dict[str, object],
        *,
        dirty: bool,
    ) -> bool:
        if not active_payload or dirty:
            return False
        return self.active_profile_fingerprint(active_payload) == self.active_profile_fingerprint(form_payload)

    def build_preview_payload(
        self,
        form_payload: dict[str, object],
        *,
        setup_id: str,
        draft_fingerprint: str,
    ) -> dict[str, object]:
        errors, warnings, infos = self.validate(form_payload)
        support_resolution = self.resolve_support(form_payload)
        support_level = str(support_resolution.get("support_level") or "blocked")
        controls = dict(support_resolution.get("controls") or {})
        messages = list(support_resolution.get("messages") or [])
        effective_executor = self.effective_executor(form_payload)
        preview_fingerprint = self.preview_fingerprint(
            form_payload,
            setup_id=setup_id,
            draft_fingerprint=draft_fingerprint,
        )
        selected = list(form_payload.get("selected_agents", []) or [])
        bindings = dict(form_payload.get("role_bindings", {}) or {})
        options = dict(form_payload.get("role_options", {}) or {})
        restart_required = self.restart_required_for_payload(self.draft_payload(form_payload))
        diff_summary = [
            f"에이전트 {', '.join(selected or ['—'])} / 구현 {bindings.get('implement') or '—'} / 검증 {bindings.get('verify') or '—'} / 자문 {bindings.get('advisory') or '—'}",
            (
                "옵션 "
                f"자문={'켜짐' if options.get('advisory_enabled') else '꺼짐'} · "
                f"operator 중지={'켜짐' if options.get('operator_stop_enabled') else '꺼짐'} · "
                f"세션 중재={'켜짐' if options.get('session_arbitration_enabled') else '꺼짐'}"
            ),
        ]
        return {
            "status": "preview_ready",
            "setup_id": setup_id,
            "schema_version": 1,
            "generated_at": utc_now_iso(),
            "draft_fingerprint": draft_fingerprint,
            "preview_fingerprint": preview_fingerprint,
            "effective_executor": effective_executor,
            "support_level": support_level,
            "controls": controls,
            "messages": messages,
            "effective_runtime_plan": support_resolution.get("effective_runtime_plan"),
            "warnings": warnings,
            "infos": infos,
            "planned_changes": {
                "write": [".pipeline/config/agent_profile.json"],
                "restart_targets": ["watcher", "launcher"] if restart_required else [],
            },
            "diff_summary": diff_summary,
            "restart_required": restart_required,
        }

    def preview_can_promote_canonical(self, state: SetupActionState, setup_id: str) -> bool:
        request_payload = read_json_path(self.paths()["request"])
        return bool(
            setup_id
            and setup_id == state.current_setup_id
            and request_payload
            and str(request_payload.get("setup_id") or "") == setup_id
        )

    def result_can_promote_canonical(self, state: SetupActionState, setup_id: str) -> bool:
        apply_payload = read_json_path(self.paths()["apply"])
        return bool(
            setup_id
            and setup_id == state.current_setup_id
            and apply_payload
            and str(apply_payload.get("setup_id") or "") == setup_id
        )

    @staticmethod
    def result_matches_current(
        result_payload: dict[str, object] | None,
        *,
        current_setup_id: str,
        current_preview_fingerprint: str,
    ) -> bool:
        if not result_payload or not current_setup_id:
            return False
        if str(result_payload.get("setup_id") or "") != current_setup_id:
            return False
        approved = str(result_payload.get("approved_preview_fingerprint") or "")
        if current_preview_fingerprint and approved and approved != current_preview_fingerprint:
            return False
        return True

    def execute_preview_roundtrip(
        self,
        state: SetupActionState,
        request_payload: dict[str, object],
        form_payload: dict[str, object],
        on_complete: Callable[[], None],
    ) -> None:
        self.executor_adapter.dispatch_preview(
            destination=self.paths()["preview"],
            build_payload=lambda: self.build_preview_payload(
                form_payload,
                setup_id=str(request_payload.get("setup_id") or ""),
                draft_fingerprint=str(request_payload.get("draft_fingerprint") or ""),
            ),
            write_json=self.write_json,
            should_promote=lambda setup_id: self.preview_can_promote_canonical(state, setup_id),
            protected_setup_ids=lambda **kwargs: self.protected_staged_setup_ids(state, **kwargs),
            on_complete=on_complete,
        )

    def execute_apply_roundtrip(
        self,
        state: SetupActionState,
        apply_payload: dict[str, object],
        form_payload: dict[str, object],
        preview_payload: dict[str, object],
        current_draft_fingerprint: str,
        on_complete: Callable[[], None],
    ) -> None:
        self.executor_adapter.dispatch_result(
            destination=self.paths()["result"],
            build_payload=lambda: {
                "status": "applied",
                "setup_id": str(apply_payload.get("setup_id") or ""),
                "schema_version": 1,
                "finished_at": utc_now_iso(),
                "approved_preview_fingerprint": str(apply_payload.get("approved_preview_fingerprint") or ""),
                "effective_executor": self.effective_executor(form_payload),
                "restart_required": bool(preview_payload.get("restart_required")),
                "draft_fingerprint": current_draft_fingerprint,
                "message": self.default_apply_result_message,
            },
            write_json=self.write_json,
            should_promote=lambda setup_id: self.result_can_promote_canonical(state, setup_id),
            protected_setup_ids=lambda **kwargs: self.protected_staged_setup_ids(state, **kwargs),
            on_complete=on_complete,
        )

    def result_feedback_lines(
        self,
        result_payload: dict[str, object] | None,
        *,
        current_setup_id: str,
    ) -> list[str]:
        if not result_payload or str(result_payload.get("setup_id") or "") != current_setup_id:
            return []
        lines: list[str] = []
        status = str(result_payload.get("status") or "")
        errors = list(result_payload.get("errors") or [])
        warnings = list(result_payload.get("warnings") or [])
        infos = list(result_payload.get("infos") or [])
        message = str(result_payload.get("message") or "").strip()
        if status == "apply_failed":
            if errors:
                lines.extend(f"오류: {msg}" for msg in errors if str(msg).strip())
            if message:
                lines.append(f"오류: {message}")
            if not errors and not message:
                lines.append("오류: 설정 적용이 실패했습니다.")
        else:
            if errors:
                lines.extend(f"오류: {msg}" for msg in errors if str(msg).strip())
            if message and message != self.default_apply_result_message:
                lines.append(f"안내: {message}")
        if warnings:
            lines.extend(f"경고: {msg}" for msg in warnings if str(msg).strip())
        if infos:
            lines.extend(f"안내: {msg}" for msg in infos if str(msg).strip())
        return lines

    def sync_last_applied_record(
        self,
        *,
        active_payload: dict[str, object],
        result_payload: dict[str, object],
        fallback_executor: str,
    ) -> dict[str, object]:
        record = build_last_applied_record(
            setup_id=str(result_payload.get("setup_id") or ""),
            approved_preview_fingerprint=str(result_payload.get("approved_preview_fingerprint") or ""),
            active_payload=active_payload,
            restart_required=bool(result_payload.get("restart_required")),
            executor=str(result_payload.get("effective_executor") or fallback_executor or "auto"),
            applied_at=str(result_payload.get("finished_at") or utc_now_iso()),
        )
        path = self.paths()["last_applied"]
        current_payload = read_json_path(path)
        if current_payload != record:
            self.write_json(path, record)
        return record

    @staticmethod
    def result_replays_last_applied(
        result_payload: dict[str, object] | None,
        last_applied_payload: dict[str, object] | None,
        *,
        active_exists: bool,
    ) -> bool:
        if active_exists or not result_payload or not isinstance(last_applied_payload, dict):
            return False
        result_setup_id = str(result_payload.get("setup_id") or "").strip()
        result_approved = str(result_payload.get("approved_preview_fingerprint") or "").strip()
        return bool(
            result_setup_id
            and result_approved
            and result_setup_id == str(last_applied_payload.get("setup_id") or "").strip()
            and result_approved == str(last_applied_payload.get("approved_preview_fingerprint") or "").strip()
        )

    def reconcile_last_applied(
        self,
        *,
        active_payload: dict[str, object] | None = None,
        last_applied_payload: dict[str, object] | None = None,
        active_exists: bool | None = None,
        last_applied_exists: bool | None = None,
    ) -> dict[str, object]:
        paths = self.paths()
        active_path = paths["active"]
        last_applied_path = paths["last_applied"]
        return reconcile_last_applied(
            active_payload=read_json_path(active_path) if active_payload is None else active_payload,
            last_applied_payload=read_json_path(last_applied_path) if last_applied_payload is None else last_applied_payload,
            active_exists=path_exists(active_path) if active_exists is None else active_exists,
            last_applied_exists=path_exists(last_applied_path) if last_applied_exists is None else last_applied_exists,
        )

    @staticmethod
    def last_applied_feedback_lines(reconciliation: dict[str, object]) -> list[str]:
        status = str(reconciliation.get("status") or "")
        setup_id = str(reconciliation.get("setup_id") or "").strip()
        executor = str(reconciliation.get("executor") or "").strip()
        prefix = f"최근 적용 기록({setup_id}" if setup_id else "최근 적용 기록("
        if setup_id and executor:
            prefix += f", 실행자 {executor}"
        elif executor:
            prefix += f"실행자 {executor}"
        prefix += ")"
        if status == "ok" and bool(reconciliation.get("restart_required")):
            return [f"안내: {prefix}이 active profile과 일치합니다."]
        if status == "mismatch":
            if not str(reconciliation.get("current_active_profile_fingerprint") or "").strip():
                return [f"경고: {prefix}은 있지만 active profile이 없습니다. 설정을 다시 적용하거나 active profile을 복구해 주세요."]
            return [f"경고: {prefix}과 active profile이 다릅니다. preview/apply를 다시 확인해 주세요."]
        if status == "broken":
            return ["오류: 최근 적용 기록을 확인할 수 없어 restart reconciliation을 완료하지 못했습니다."]
        return []

    @staticmethod
    def last_applied_notice_text(
        reconciliation: dict[str, object],
        *,
        state: str,
        restart_required: bool,
    ) -> str:
        if state == "Applied" and restart_required:
            return "설정 적용이 끝났습니다. active profile을 읽으려면 watcher/launcher를 재시작하세요."
        status = str(reconciliation.get("status") or "")
        if status == "ok" and bool(reconciliation.get("restart_required")):
            return "최근 적용 기록이 active profile과 일치합니다."
        if status == "mismatch":
            if not str(reconciliation.get("current_active_profile_fingerprint") or "").strip():
                return "최근 적용 기록은 있지만 active profile이 없어 recovery가 필요합니다."
            return "최근 적용 기록과 active profile이 달라 restart reconciliation이 필요합니다."
        if status == "broken":
            return "최근 적용 기록을 읽지 못해 restart reconciliation을 확인할 수 없습니다."
        return ""

    def build_fast_snapshot(
        self,
        form_payload: dict[str, object],
        state: SetupActionState,
    ) -> SetupFastSnapshot:
        current_draft_fingerprint = self.fingerprint(self.draft_payload(form_payload))
        disk_state = self.read_disk_state()
        draft_payload = disk_state.draft_payload
        active_payload = disk_state.active_payload
        errors, warnings, infos = self.validate(form_payload)
        support_resolution = self.resolve_support(form_payload)
        runtime_resolution = self.resolve_runtime_active_profile()
        draft_saved = bool(draft_payload and self.fingerprint(draft_payload) == current_draft_fingerprint)
        active_matches_current = self.active_matches_current_form(active_payload, form_payload, dirty=state.dirty)
        fast_state = "DraftOnly"
        if errors:
            fast_state = "InvalidConfig"
        elif disk_state.apply_exists:
            fast_state = "ApplyPending"
        elif disk_state.request_exists:
            fast_state = "PreviewWaiting"
        elif active_matches_current:
            fast_state = "Applied"
        disk_has_detail_truth = any(
            getattr(disk_state, flag)
            for flag in ("preview_exists", "result_exists", "last_applied_exists")
        )
        state_text = {
            "DraftOnly": "초안 상태",
            "PreviewWaiting": "미리보기 대기 중",
            "PreviewReady": "미리보기 준비됨",
            "ApplyPending": "적용 진행 중",
            "RecoveryNeeded": "복구 필요",
            "ApplyFailed": "적용 실패",
            "Applied": "적용 완료",
            "InvalidConfig": "잘못된 설정",
        }.get(fast_state, fast_state)
        if fast_state in {"PreviewWaiting", "ApplyPending"} or disk_has_detail_truth:
            state_text = "상태 확인 중..."
        return SetupFastSnapshot(
            form_payload=form_payload,
            current_draft_fingerprint=current_draft_fingerprint,
            draft_saved=draft_saved,
            errors=errors,
            warnings=warnings,
            infos=infos,
            support_resolution=support_resolution,
            runtime_resolution=runtime_resolution,
            fast_state=fast_state,
            state_text=state_text,
            action_pending=fast_state in {"PreviewWaiting", "ApplyPending"},
            active_matches_current=active_matches_current,
            current_setup_id_text=state.current_setup_id or "—",
            current_preview_fingerprint_text=state.current_preview_fingerprint or "—",
        )

    def build_detail_snapshot(
        self,
        form_payload: dict[str, object],
        state: SetupActionState,
    ) -> SetupDetailSnapshot:
        current_draft_fingerprint = self.fingerprint(self.draft_payload(form_payload))
        disk_state = self.read_disk_state()
        draft_payload = disk_state.draft_payload
        request_payload = disk_state.request_payload
        preview_payload = disk_state.preview_payload
        apply_payload = disk_state.apply_payload
        result_payload = disk_state.result_payload
        active_payload = disk_state.active_payload
        last_applied_payload = disk_state.last_applied_payload
        disk_setup_truth_exists = any(
            getattr(disk_state, flag)
            for flag in (
                "active_exists",
                "request_exists",
                "preview_exists",
                "apply_exists",
                "result_exists",
                "last_applied_exists",
            )
        )
        current_setup_id = state.current_setup_id if disk_setup_truth_exists else ""
        cached_preview_payload = state.current_preview_payload if disk_setup_truth_exists else None
        cached_result_payload = state.current_result_payload if disk_setup_truth_exists else None
        draft_saved = bool(draft_payload and self.fingerprint(draft_payload) == current_draft_fingerprint)

        errors, warnings, infos = self.validate(form_payload)
        support_resolution = self.resolve_support(form_payload)

        request_current = bool(
            request_payload
            and str(request_payload.get("setup_id") or "") == current_setup_id
            and str(request_payload.get("draft_fingerprint") or "") == current_draft_fingerprint
        )
        current_request_payload = request_payload if request_current else None

        canonical_preview_current = self.preview_matches_current(
            preview_payload, current_setup_id, current_draft_fingerprint
        )
        cached_preview_current = self.preview_matches_current(
            cached_preview_payload, current_setup_id, current_draft_fingerprint
        )
        stale_preview = bool(preview_payload) and not canonical_preview_current
        preview_current = False
        current_preview_payload: dict[str, object] | None = None
        current_preview_fingerprint = ""
        if canonical_preview_current and preview_payload:
            preview_current = True
            current_preview_payload = preview_payload
        elif cached_preview_current and cached_preview_payload:
            preview_current = True
            current_preview_payload = cached_preview_payload
        if current_preview_payload:
            current_preview_fingerprint = str(current_preview_payload.get("preview_fingerprint") or "")

        apply_current = bool(
            apply_payload
            and str(apply_payload.get("setup_id") or "") == current_setup_id
            and str(apply_payload.get("approved_preview_fingerprint") or "") == current_preview_fingerprint
        )
        current_apply_payload = apply_payload if apply_current else None

        promotion_failed = False
        promotion_failed_message = ""
        current_result_payload: dict[str, object] | None = None
        restart_required = False
        canonical_result_current = self.result_matches_current(
            result_payload,
            current_setup_id=current_setup_id,
            current_preview_fingerprint=current_preview_fingerprint,
        )
        cached_result_current = self.result_matches_current(
            cached_result_payload,
            current_setup_id=current_setup_id,
            current_preview_fingerprint=current_preview_fingerprint,
        )
        if canonical_result_current and result_payload:
            current_result_payload = result_payload
        elif cached_result_current and cached_result_payload:
            current_result_payload = cached_result_payload

        if current_result_payload:
            replayed_result = self.result_replays_last_applied(
                current_result_payload,
                last_applied_payload,
                active_exists=disk_state.active_exists,
            )
            can_promote = False
            if replayed_result:
                restart_required = False
            else:
                can_promote, promotion_failed_message = self.result_can_promote_active(
                    current_result_payload,
                    current_apply_payload,
                    current_preview_payload,
                    current_setup_id,
                    draft_payload,
                    current_draft_fingerprint,
                    self.fingerprint,
                )
            if not replayed_result and can_promote:
                promoted_active_payload = self.active_payload(
                    draft_payload,
                    source_setup_id=current_setup_id,
                )
                self.write_json(self.paths()["active"], promoted_active_payload)
                active_payload = promoted_active_payload
                disk_state.active_payload = promoted_active_payload
                disk_state.active_exists = True
                last_applied_payload = self.sync_last_applied_record(
                    active_payload=promoted_active_payload,
                    result_payload=current_result_payload,
                    fallback_executor=self.effective_executor(form_payload),
                )
                restart_required = bool(current_result_payload.get("restart_required"))
            elif not replayed_result and str(current_result_payload.get("status") or "") == "applied":
                promotion_failed = True

        active_matches_current = self.active_matches_current_form(active_payload, form_payload, dirty=state.dirty)

        current_state = "DraftOnly"
        if errors:
            current_state = "InvalidConfig"
        elif apply_current and current_result_payload is None:
            current_state = "ApplyPending"
        elif (
            current_result_payload is not None
            and str(current_result_payload.get("status") or "") == "apply_failed"
        ) or promotion_failed:
            current_state = "ApplyFailed"
        elif (
            current_result_payload is not None
            and str(current_result_payload.get("status") or "") == "applied"
            and not promotion_failed
        ):
            current_state = "Applied"
        elif active_matches_current:
            current_state = "Applied"
        elif preview_current:
            current_state = "PreviewReady"
        elif request_current:
            current_state = "PreviewWaiting"

        reconciliation = self.reconcile_last_applied(
            active_payload=active_payload,
            last_applied_payload=last_applied_payload,
            active_exists=disk_state.active_exists,
            last_applied_exists=disk_state.last_applied_exists,
        )
        reconciliation_status = str(reconciliation.get("status") or "")
        if current_state == "Applied" and reconciliation_status in {"mismatch", "broken"}:
            current_state = "RecoveryNeeded"

        display_support_level = str(support_resolution.get("support_level") or "blocked")
        display_controls = dict(support_resolution.get("controls") or {})
        if preview_current and current_preview_payload:
            display_support_level = str(current_preview_payload.get("support_level") or display_support_level)
            display_controls = dict(current_preview_payload.get("controls") or display_controls)

        validation_lines = self.result_feedback_lines(
            current_result_payload,
            current_setup_id=current_setup_id,
        )
        validation_lines.extend(self.support_banner_lines(display_support_level, display_controls))
        validation_lines.extend(self.last_applied_feedback_lines(reconciliation))
        validation_lines.extend(self.runtime_resolution_feedback_lines(self.resolve_runtime_active_profile()))
        if errors:
            validation_lines.extend(f"오류: {msg}" for msg in errors)
        if promotion_failed_message:
            validation_lines.append(f"오류: {promotion_failed_message}")
        if warnings:
            validation_lines.extend(f"경고: {msg}" for msg in warnings)
        if infos:
            validation_lines.extend(f"안내: {msg}" for msg in infos)

        return SetupDetailSnapshot(
            form_payload=form_payload,
            current_draft_fingerprint=current_draft_fingerprint,
            draft_saved=draft_saved,
            errors=errors,
            warnings=warnings,
            infos=infos,
            support_resolution=support_resolution,
            current_setup_id=current_setup_id,
            current_request_payload=current_request_payload,
            current_preview_payload=current_preview_payload,
            current_preview_fingerprint=current_preview_fingerprint,
            current_apply_payload=current_apply_payload,
            current_result_payload=current_result_payload,
            restart_required=restart_required,
            state=current_state,
            display_support_level=display_support_level,
            display_controls=display_controls,
            validation_text="\n".join(validation_lines) if validation_lines else "유효성 문제 없음.",
            preview_summary_text=self.summary_text(
                form_payload,
                current_preview_payload or preview_payload,
                preview_current=preview_current,
                stale_preview=stale_preview,
            ),
            restart_notice_text=self.last_applied_notice_text(
                reconciliation,
                state=current_state,
                restart_required=restart_required,
            ),
            apply_readiness_text=self.apply_readiness_text(
                current_state,
                preview_current,
                current_preview_payload,
                state=state,
            ),
        )

    def apply_readiness_text(
        self,
        state_name: str,
        preview_current: bool,
        preview_payload: dict[str, object] | None = None,
        *,
        state: SetupActionState,
    ) -> str:
        preview_controls = dict((preview_payload or {}).get("controls") or {})
        if preview_current and preview_payload and not bool(preview_controls.get("apply_allowed")):
            return "적용 비활성: 현재 프로필은 차단 상태여서 미리보기만 가능합니다"
        if state_name == "InvalidConfig":
            return "적용 비활성: 설정이 올바르지 않습니다"
        if state_name == "PreviewWaiting":
            return "적용 비활성: 현재 초안 기준 미리보기를 기다리는 중입니다"
        if state_name == "ApplyPending":
            return "적용 비활성: 이미 적용이 진행 중입니다"
        if state_name == "RecoveryNeeded":
            if preview_current and preview_payload and bool(preview_controls.get("apply_allowed")):
                return "적용 가능: active profile 복구를 위해 현재 미리보기를 다시 적용할 수 있습니다"
            return "적용 비활성: active profile 복구를 위해 미리보기를 다시 생성하세요"
        if state_name == "Applied" and not state.dirty:
            return "적용 비활성: active profile이 현재 초안과 이미 같습니다"
        if not preview_current:
            if state.dirty or not state.draft_saved:
                return "적용 비활성: 현재 초안을 저장하거나 미리보기를 다시 생성하세요"
            return "적용 비활성: 미리보기를 기다리는 중입니다"
        return "적용 가능: 미리보기가 현재 초안과 일치합니다"
