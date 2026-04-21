from __future__ import annotations

import tempfile
import threading
import time
import unittest
from unittest import mock
from pathlib import Path

from pipeline_gui.app import PipelineGUI
from pipeline_gui.home_controller import HomeController
from pipeline_gui.setup_controller import SetupController
from pipeline_gui.setup_executor import FaultInjectingSetupExecutorAdapter, LocalSetupExecutorAdapter
from pipeline_gui.setup_models import SetupActionState
from pipeline_gui.setup_profile import build_last_applied_record
from pipeline_runtime.lane_catalog import default_role_bindings
from storage.json_store_base import read_json


class _Var:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def set(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        return self.value


class _Widget:
    def __init__(self) -> None:
        self.state = None
        self._fg = None
        self._bg = None
        self._highlightbackground = None
        self.packed = False

    def configure(self, **kwargs: object) -> None:
        if "state" in kwargs:
            self.state = kwargs["state"]
        if "fg" in kwargs:
            self._fg = kwargs["fg"]
        if "bg" in kwargs:
            self._bg = kwargs["bg"]
        if "highlightbackground" in kwargs:
            self._highlightbackground = kwargs["highlightbackground"]

    def pack(self, *_args: object, **_kwargs: object) -> None:
        self.packed = True

    def pack_forget(self) -> None:
        self.packed = False


class _FakeRoot:
    def __init__(self) -> None:
        self._next_id = 0
        self.pending: dict[str, object] = {}
        self.cancelled: list[str] = []

    def after(self, _delay: int, callback=None):
        self._next_id += 1
        token = f"after-{self._next_id}"
        if callback is not None:
            self.pending[token] = callback
        return token

    def after_idle(self, callback=None):
        self._next_id += 1
        token = f"idle-{self._next_id}"
        if callback is not None:
            self.pending[token] = callback
        return token

    def after_cancel(self, token: str) -> None:
        self.cancelled.append(token)
        self.pending.pop(token, None)

    def run(self, token: str) -> None:
        callback = self.pending.pop(token, None)
        if callback is not None:
            callback()

    def run_all(self) -> None:
        while self.pending:
            token = next(iter(self.pending))
            self.run(token)


def _make_setup_gui(project: Path, *, adapter=None) -> PipelineGUI:
    gui = PipelineGUI.__new__(PipelineGUI)
    gui.project = project
    gui._session_name = "aip-test"
    gui._mode = "home"
    gui._project_valid = True
    gui._action_in_progress = False
    gui._last_snapshot = {"session_ok": False}
    gui._setup_form_updating = False
    gui._setup_state = "ready"
    gui._setup_state_detail = ""
    gui._setup_state_model = SetupActionState()
    gui._setup_state_model.detail_ready = True
    gui._setup_snapshot_refresh_last_at = 0.0
    gui._setup_snapshot_refresh_ttl_sec = 2.0
    gui._setup_refresh_after_id = None
    gui._setup_detail_after_id = None
    gui._setup_refresh_generation = 0
    gui._setup_executor_adapter = adapter or LocalSetupExecutorAdapter(
        preview_delay_sec=0.01,
        result_delay_sec=0.01,
    )
    gui._setup_controller = SetupController(
        project,
        executor_adapter=gui._setup_executor_adapter,
    )
    gui._home_controller = HomeController(project, gui._session_name)
    gui._setup_agent_vars = {name: _Var(True) for name in ("Claude", "Codex", "Gemini")}
    default_bindings = default_role_bindings()
    gui._setup_implement_var = _Var(default_bindings["implement"])
    gui._setup_verify_var = _Var(default_bindings["verify"])
    gui._setup_advisory_var = _Var(default_bindings["advisory"])
    gui._setup_advisory_enabled_var = _Var(True)
    gui._setup_operator_stop_enabled_var = _Var(True)
    gui._setup_session_arbitration_var = _Var(True)
    gui._setup_self_verify_var = _Var(False)
    gui._setup_self_advisory_var = _Var(False)
    gui._setup_executor_var = _Var("auto")
    gui._setup_agent_error_var = _Var("")
    gui._setup_implement_error_var = _Var("")
    gui._setup_verify_error_var = _Var("")
    gui._setup_advisory_error_var = _Var("")
    gui._setup_mode_state_var = _Var("")
    gui._setup_support_level_var = _Var("")
    gui._setup_runtime_profile_var = _Var("")
    gui._setup_support_label = _Widget()
    gui._setup_runtime_profile_label = _Widget()
    gui._setup_validation_var = _Var("")
    gui._setup_preview_summary_var = _Var("")
    gui._setup_current_setup_id_var = _Var("—")
    gui._setup_current_preview_fingerprint_var = _Var("—")
    gui._setup_apply_readiness_var = _Var("")
    gui._setup_restart_notice_var = _Var("")
    gui._setup_cleanup_summary_var = _Var("아직 정리 기록이 없습니다.")
    gui._runtime_launch_var = _Var("")
    gui._runtime_launch_label = _Widget()
    gui.setup_var = _Var("")
    gui.setup_state_label = _Widget()
    gui.btn_start = _Widget()
    gui.btn_stop = _Widget()
    gui.btn_restart = _Widget()
    gui.btn_attach = _Widget()
    gui.btn_token_backfill = _Widget()
    gui.btn_token_rebuild = _Widget()
    gui.btn_setup_save_draft = _Widget()
    gui.btn_setup_generate_preview = _Widget()
    gui.btn_setup_apply = _Widget()
    gui.btn_setup_clean_staged = _Widget()
    gui.btn_setup_restart_now = _Widget()
    gui._lock_buttons = mock.Mock()
    gui._unlock_buttons = mock.Mock()
    gui._set_toast_style = mock.Mock()
    gui.msg_var = _Var("")
    gui._clear_msg_later = mock.Mock()
    gui._ask_yn = mock.Mock(return_value=True)
    gui._on_restart = mock.Mock()
    for name in (
        "_setup_paths",
        "_setup_default_profile",
        "_setup_selected_agents",
        "_setup_recommended_executor",
        "_setup_collect_form_payload",
        "_setup_draft_payload",
        "_setup_active_payload",
        "_setup_payload_for_fingerprint",
        "_setup_fingerprint",
        "_setup_active_profile_fingerprint",
        "_setup_preview_fingerprint",
        "_setup_resolve_support",
        "_resolve_runtime_active_profile",
        "_setup_state_presentation",
        "_apply_setup_state_presentation",
        "_apply_runtime_launch_presentation",
        "_runtime_launch_allowed",
        "_setup_support_banner_lines",
        "_setup_validate",
        "_setup_effective_executor",
        "_setup_write_json",
        "_setup_apply_inline_errors",
        "_setup_summary_text",
        "_setup_restart_required_for_payload",
        "_setup_cleanup_staged_files_once_on_startup",
        "_setup_cleanup_staged_files",
        "_setup_reset_cleanup_history",
        "_setup_record_cleanup_result",
        "_setup_build_preview_payload",
        "_setup_execute_preview_roundtrip",
        "_setup_execute_apply_roundtrip",
        "_setup_sync_last_applied_record",
        "_setup_reconcile_last_applied",
        "_setup_last_applied_feedback_lines",
        "_setup_last_applied_notice_text",
        "_refresh_setup_mode_state",
        "_refresh_setup_mode_state_if_due",
        "_setup_apply_readiness_text",
        "_sync_start_button_state",
        "_update_setup_action_buttons",
        "_setup_promote_active_profile",
        "_setup_generate_setup_id",
        "_update_setup_widget_options",
        "_on_setup_clean_staged",
        "_on_setup_save_draft",
        "_on_setup_generate_preview",
        "_on_setup_apply",
        "_on_setup_confirm_restart",
        "_set_main_button_states",
        "_on_start",
    ):
        setattr(gui, name, getattr(PipelineGUI, name).__get__(gui, PipelineGUI))
    gui._on_restart = mock.Mock()
    gui._setup_preview_matches_current = PipelineGUI._setup_preview_matches_current
    gui._setup_result_can_promote_active = PipelineGUI._setup_result_can_promote_active
    return gui


def _wait_until(predicate, *, timeout: float = 0.5) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def _setup_state(gui: PipelineGUI) -> SetupActionState:
    return PipelineGUI._export_setup_state(gui)


def _update_setup_state(gui: PipelineGUI, **updates: object) -> SetupActionState:
    state = _setup_state(gui)
    for key, value in updates.items():
        setattr(state, key, value)
    PipelineGUI._apply_setup_state_model(gui, state)
    return state


class PipelineGuiAppTest(unittest.TestCase):
    def test_do_start_timeout_includes_start_log_hint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            script = gui.project / "start-pipeline.sh"
            script.write_text("#!/bin/bash\n", encoding="utf-8")

            class _Root:
                @staticmethod
                def after(_delay: int, callback=None):
                    if callback is not None:
                        callback()

            gui.root = _Root()

            with (
                mock.patch("pipeline_gui.app.resolve_project_runtime_file", return_value=script),
                mock.patch("pipeline_gui.app.pipeline_start", return_value="시작 요청됨"),
                mock.patch(
                    "pipeline_gui.app.confirm_pipeline_start",
                    return_value=(
                        False,
                        "시작 실패: 15초 안에 tmux 세션 'aip-test'가 감지되지 않았습니다 — Launch blocked: Active profile is missing.",
                    ),
                ),
            ):
                PipelineGUI._do_start(gui)

            message = gui._unlock_buttons.call_args.args[0]
            self.assertIn("Launch blocked: Active profile is missing.", message)
            self.assertIn("aip-test", message)

    def test_do_start_accepts_fresh_watcher_start_when_tmux_probe_misses(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            script = gui.project / "start-pipeline.sh"
            script.write_text("#!/bin/bash\n", encoding="utf-8")

            class _Root:
                @staticmethod
                def after(_delay: int, callback=None):
                    if callback is not None:
                        callback()

            gui.root = _Root()

            with (
                mock.patch("pipeline_gui.app.resolve_project_runtime_file", return_value=script),
                mock.patch("pipeline_gui.app.pipeline_start", return_value="시작 요청됨"),
                mock.patch(
                    "pipeline_gui.app.confirm_pipeline_start",
                    return_value=(True, "파이프라인 시작 완료 (watcher 확인)"),
                ),
            ):
                PipelineGUI._do_start(gui)

            message = gui._unlock_buttons.call_args.args[0]
            self.assertIn("watcher 확인", message)

    def test_setup_roundtrip_writes_preview_and_result_and_updates_meta_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            gui._set_toast_style.assert_called_with("progress")

            self.assertEqual(_setup_state(gui).mode_state, "PreviewWaiting")
            self.assertIsNotNone(_setup_state(gui).current_request_payload)
            self.assertEqual(
                _setup_state(gui).current_setup_id,
                str((_setup_state(gui).current_request_payload or {}).get("setup_id") or ""),
            )

            paths = gui._setup_paths()
            self.assertTrue(_wait_until(lambda: read_json(paths["preview"]) is not None))
            self.assertTrue(
                _wait_until(
                    lambda: (gui._refresh_setup_mode_state() or True) and _setup_state(gui).mode_state == "PreviewReady",
                    timeout=1.5,
                )
            )
            preview_payload = read_json(paths["preview"])
            self.assertIsNotNone(read_json(paths["request"]))
            self.assertTrue(
                PipelineGUI._setup_preview_matches_current(
                    preview_payload,
                    _setup_state(gui).current_setup_id,
                    _setup_state(gui).current_draft_fingerprint,
                )
            )
            self.assertTrue(
                _wait_until(lambda: _setup_state(gui).mode_state == "PreviewReady", timeout=1.5)
            )
            self.assertTrue(
                _wait_until(lambda: gui._setup_current_setup_id_var.get() != "—", timeout=1.5)
            )
            self.assertTrue(
                _wait_until(
                    lambda: gui._setup_current_preview_fingerprint_var.get().startswith("sha256:"),
                    timeout=1.5,
                )
            )

            PipelineGUI._on_setup_apply(gui)
            gui._set_toast_style.assert_called_with("progress")
            self.assertEqual(_setup_state(gui).mode_state, "ApplyPending")
            self.assertIsNotNone(_setup_state(gui).current_apply_payload)
            self.assertEqual(
                _setup_state(gui).current_preview_fingerprint,
                gui._setup_current_preview_fingerprint_var.get(),
            )

            self.assertTrue(_wait_until(lambda: read_json(paths["result"]) is not None))
            self.assertTrue(
                _wait_until(
                    lambda: (gui._refresh_setup_mode_state() or True) and _setup_state(gui).mode_state == "Applied",
                    timeout=1.5,
                )
            )
            result_payload = read_json(paths["result"])
            active_payload = read_json(paths["active"])
            last_applied_payload = read_json(paths["last_applied"])
            self.assertEqual(result_payload["status"], "applied")
            self.assertEqual(_setup_state(gui).mode_state, "Applied")
            self.assertIsNotNone(active_payload)
            self.assertIsNotNone(last_applied_payload)
            self.assertEqual(last_applied_payload["setup_id"], result_payload["setup_id"])
            self.assertEqual(
                last_applied_payload["approved_preview_fingerprint"],
                result_payload["approved_preview_fingerprint"],
            )
            self.assertEqual(
                last_applied_payload["active_profile_fingerprint"],
                gui._setup_active_profile_fingerprint(active_payload),
            )
            self.assertEqual(last_applied_payload["executor"], result_payload["effective_executor"])
            self.assertEqual(gui.btn_setup_restart_now.state, "normal")
            self.assertNotIn("설정 적용 결과가 도착했습니다.", gui._setup_validation_var.get())
            self.assertEqual(
                gui._setup_restart_notice_var.get(),
                "설정 적용이 끝났습니다. active profile을 읽으려면 watcher/launcher를 재시작하세요.",
            )

    def test_setup_refresh_reports_last_applied_reconciliation_success_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            gui = _make_setup_gui(project)
            active_payload = gui._setup_active_payload(gui._setup_default_profile(), source_setup_id="setup-1")
            gui._setup_write_json(gui._setup_paths()["active"], active_payload)
            gui._setup_write_json(
                gui._setup_paths()["last_applied"],
                build_last_applied_record(
                    setup_id="setup-1",
                    approved_preview_fingerprint="sha256:preview-1",
                    active_payload=active_payload,
                    restart_required=True,
                    executor="Codex",
                    applied_at="2026-04-09T00:00:00+00:00",
                ),
            )

            PipelineGUI._load_setup_form_from_disk(gui)
            gui._refresh_setup_mode_state()

            self.assertEqual(gui._setup_restart_notice_var.get(), "최근 적용 기록이 active profile과 일치합니다.")
            self.assertIn("active profile과 일치합니다", gui._setup_validation_var.get())

    def test_setup_refresh_reports_last_applied_reconciliation_mismatch_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            gui = _make_setup_gui(project)
            active_payload = gui._setup_active_payload(gui._setup_default_profile(), source_setup_id="setup-2")
            gui._setup_write_json(gui._setup_paths()["active"], active_payload)
            gui._setup_write_json(
                gui._setup_paths()["last_applied"],
                {
                    "setup_id": "setup-1",
                    "approved_preview_fingerprint": "sha256:preview-old",
                    "active_profile_fingerprint": "sha256:stale",
                    "applied_at": "2026-04-09T00:00:00+00:00",
                    "restart_required": True,
                    "executor": "Codex",
                },
            )

            PipelineGUI._load_setup_form_from_disk(gui)
            gui._refresh_setup_mode_state()

            self.assertEqual(
                gui._setup_restart_notice_var.get(),
                "최근 적용 기록과 active profile이 달라 restart reconciliation이 필요합니다.",
            )
            self.assertIn("preview/apply를 다시 확인해 주세요", gui._setup_validation_var.get())

    def test_setup_refresh_reports_missing_active_profile_when_last_applied_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            gui = _make_setup_gui(project)
            gui._setup_write_json(
                gui._setup_paths()["last_applied"],
                {
                    "setup_id": "setup-1",
                    "approved_preview_fingerprint": "sha256:preview-old",
                    "active_profile_fingerprint": "sha256:stale",
                    "applied_at": "2026-04-09T00:00:00+00:00",
                    "restart_required": True,
                    "executor": "Codex",
                },
            )

            gui._refresh_setup_mode_state()

            self.assertEqual(
                gui._setup_restart_notice_var.get(),
                "최근 적용 기록은 있지만 active profile이 없어 recovery가 필요합니다.",
            )
            self.assertIn("active profile이 없습니다", gui._setup_validation_var.get())

    def test_setup_refresh_downgrades_cached_applied_state_when_active_profile_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            self.assertTrue(
                _wait_until(
                    lambda: (gui._refresh_setup_mode_state() or True) and _setup_state(gui).mode_state == "PreviewReady",
                    timeout=0.6,
                )
            )
            PipelineGUI._on_setup_apply(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["result"]) is not None))
            self.assertTrue(
                _wait_until(
                    lambda: (gui._refresh_setup_mode_state() or True) and _setup_state(gui).mode_state == "Applied",
                    timeout=0.6,
                )
            )

            self.assertTrue(_wait_until(lambda: _setup_state(gui).mode_state == "Applied", timeout=1.5))

            gui._setup_paths()["active"].unlink()
            gui._refresh_setup_mode_state()

            self.assertEqual(_setup_state(gui).mode_state, "RecoveryNeeded")
            self.assertEqual(gui._setup_mode_state_var.get(), "복구 필요")
            self.assertEqual(
                gui._setup_restart_notice_var.get(),
                "최근 적용 기록은 있지만 active profile이 없어 recovery가 필요합니다.",
            )
            self.assertIn("active profile이 없습니다", gui._setup_validation_var.get())
            self.assertEqual(
                gui._setup_apply_readiness_var.get(),
                "적용 가능: active profile 복구를 위해 현재 미리보기를 다시 적용할 수 있습니다",
            )
            self.assertEqual(gui.btn_setup_restart_now.state, "disabled")

    def test_setup_refresh_clears_cached_applied_state_when_disk_truth_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            self.assertTrue(
                _wait_until(
                    lambda: (gui._refresh_setup_mode_state() or True) and _setup_state(gui).mode_state == "PreviewReady",
                    timeout=1.5,
                )
            )
            PipelineGUI._on_setup_apply(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["result"]) is not None))
            self.assertTrue(
                _wait_until(
                    lambda: (gui._refresh_setup_mode_state() or True) and _setup_state(gui).mode_state == "Applied",
                    timeout=1.5,
                )
            )

            self.assertEqual(_setup_state(gui).mode_state, "Applied")

            for key in ("active", "request", "preview", "apply", "result", "last_applied"):
                path = gui._setup_paths()[key]
                if path.exists():
                    path.unlink()

            gui._refresh_setup_mode_state()

            self.assertEqual(_setup_state(gui).mode_state, "DraftOnly")
            self.assertEqual(gui._setup_mode_state_var.get(), "초안 상태")
            self.assertEqual(gui._setup_current_setup_id_var.get(), "—")
            self.assertEqual(gui._setup_current_preview_fingerprint_var.get(), "—")
            self.assertEqual(gui._setup_restart_notice_var.get(), "")
            self.assertNotIn("설정 적용 결과가 도착했습니다.", gui._setup_validation_var.get())
            self.assertIsNone(_setup_state(gui).current_result_payload)

    def test_setup_refresh_uses_active_profile_as_applied_truth_without_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            gui = _make_setup_gui(project)
            active_payload = gui._setup_active_payload(gui._setup_default_profile(), source_setup_id="setup-1")
            gui._setup_write_json(gui._setup_paths()["active"], active_payload)

            PipelineGUI._load_setup_form_from_disk(gui)
            gui._refresh_setup_mode_state()

            self.assertEqual(_setup_state(gui).mode_state, "Applied")
            self.assertEqual(gui._setup_mode_state_var.get(), "적용 완료")
            self.assertEqual(gui._setup_current_setup_id_var.get(), "—")
            self.assertEqual(gui._setup_current_preview_fingerprint_var.get(), "—")
            self.assertEqual(
                gui._setup_apply_readiness_var.get(),
                "적용 비활성: active profile이 현재 초안과 이미 같습니다",
            )

    def test_setup_blocked_preview_uses_foundation_controls_and_disables_apply(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            for name, var in gui._setup_agent_vars.items():
                var.set(name == "Codex")
            gui._setup_implement_var.set("Codex")
            gui._setup_verify_var.set("Codex")
            gui._setup_advisory_enabled_var.set(False)
            gui._setup_advisory_var.set("")
            gui._setup_self_verify_var.set(False)
            _update_setup_state(gui, dirty=True)
            gui._refresh_setup_mode_state()

            PipelineGUI._on_setup_generate_preview(gui)

            paths = gui._setup_paths()
            self.assertTrue(_wait_until(lambda: read_json(paths["preview"]) is not None))
            gui._refresh_setup_mode_state()
            preview_payload = read_json(paths["preview"])
            request_payload = read_json(paths["request"])

            self.assertIsNotNone(preview_payload)
            self.assertIsNotNone(request_payload)
            self.assertEqual(preview_payload["support_level"], "blocked")
            self.assertNotIn("support_level_label", preview_payload)
            self.assertTrue(preview_payload["controls"]["preview_allowed"])
            self.assertFalse(preview_payload["controls"]["apply_allowed"])
            self.assertEqual(request_payload["support_level"], "blocked")
            self.assertFalse(request_payload["controls"]["apply_allowed"])
            self.assertEqual(gui._setup_support_level_var.get(), "차단")
            self.assertEqual(gui._setup_support_label._fg, "#f87171")
            self.assertEqual(gui.btn_setup_apply.state, "disabled")
            self.assertEqual(gui._setup_apply_readiness_var.get(), "적용 비활성: 현재 프로필은 차단 상태여서 미리보기만 가능합니다")
            self.assertIn("현재 프로필은 차단 상태입니다", gui._setup_validation_var.get())

    def test_setup_experimental_preview_shows_banner_and_keeps_apply_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            for name, var in gui._setup_agent_vars.items():
                var.set(name == "Codex")
            gui._setup_implement_var.set("Codex")
            gui._setup_verify_var.set("Codex")
            gui._setup_advisory_enabled_var.set(False)
            gui._setup_advisory_var.set("")
            gui._setup_self_verify_var.set(True)
            _update_setup_state(gui, dirty=True)
            gui._refresh_setup_mode_state()

            PipelineGUI._on_setup_generate_preview(gui)

            paths = gui._setup_paths()
            self.assertTrue(_wait_until(lambda: read_json(paths["preview"]) is not None))
            self.assertTrue(
                _wait_until(
                    lambda: (gui._refresh_setup_mode_state() or True) and _setup_state(gui).mode_state == "PreviewReady",
                    timeout=1.5,
                )
            )
            preview_payload = read_json(paths["preview"])

            self.assertIsNotNone(preview_payload)
            self.assertEqual(preview_payload["support_level"], "experimental")
            self.assertNotIn("support_level_label", preview_payload)
            self.assertTrue(preview_payload["controls"]["banner_required"])
            self.assertEqual(gui._setup_support_level_var.get(), "실험적")
            self.assertEqual(gui._setup_support_label._fg, "#fbbf24")
            self.assertTrue(_wait_until(lambda: gui.btn_setup_apply.state == "normal", timeout=1.5))
            self.assertIn("실험적 프로필입니다", gui._setup_validation_var.get())

    def test_local_setup_executor_suppresses_stale_preview_canonical_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(preview_delay_sec=0.02, result_delay_sec=0.01)

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            first_setup_id = _setup_state(gui).current_setup_id

            gui._setup_executor_var.set("Codex")
            _update_setup_state(gui, dirty=True)
            gui._refresh_setup_mode_state()
            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            second_setup_id = _setup_state(gui).current_setup_id

            self.assertNotEqual(first_setup_id, second_setup_id)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None, timeout=0.6))
            time.sleep(0.05)
            preview_payload = read_json(gui._setup_paths()["preview"])
            self.assertEqual(preview_payload["setup_id"], second_setup_id)
            self.assertIsNotNone(read_json(gui._setup_paths()["preview"].with_name(f"preview.{first_setup_id}.staged.json")))

    def test_setup_refresh_does_not_run_automatic_cleanup_during_steady_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(
                preview_delay_sec=0.20,
                result_delay_sec=0.01,
                staged_retention_sec=0.01,
            )

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            current_setup_id = _setup_state(gui).current_setup_id
            paths = gui._setup_paths()
            keep_path = paths["preview"].with_name(f"preview.{current_setup_id}.staged.json")
            stale_path = paths["result"].with_name("result.setup-stale.staged.json")
            gui._setup_write_json(keep_path, {"setup_id": current_setup_id})
            gui._setup_write_json(stale_path, {"setup_id": "setup-stale"})

            time.sleep(0.02)
            gui._refresh_setup_mode_state()

            self.assertTrue(keep_path.exists())
            self.assertTrue(stale_path.exists())
            self.assertEqual(gui._setup_cleanup_summary_var.get(), "아직 정리 기록이 없습니다.")

    def test_setup_startup_cleanup_uses_disk_request_apply_context_to_protect_current_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(
                preview_delay_sec=0.01,
                result_delay_sec=0.01,
                staged_retention_sec=0.01,
            )
            paths = gui._setup_paths()
            gui._setup_write_json(paths["request"], {"setup_id": "setup-current"})
            gui._setup_write_json(paths["apply"], {"setup_id": "setup-apply"})
            keep_request = paths["preview"].with_name("preview.setup-current.staged.json")
            keep_apply = paths["result"].with_name("result.setup-apply.staged.json")
            stale_path = paths["preview"].with_name("preview.setup-old.staged.json")
            gui._setup_write_json(keep_request, {"setup_id": "setup-current"})
            gui._setup_write_json(keep_apply, {"setup_id": "setup-apply"})
            gui._setup_write_json(stale_path, {"setup_id": "setup-old"})

            time.sleep(0.02)
            PipelineGUI._setup_cleanup_staged_files_once_on_startup(gui)

            self.assertTrue(keep_request.exists())
            self.assertTrue(keep_apply.exists())
            self.assertFalse(stale_path.exists())
            self.assertEqual(gui._setup_cleanup_summary_var.get(), "초기 정리: 오래된 setup 파일 1개 정리")

    def test_setup_startup_cleanup_keeps_last_applied_result_and_removes_stale_canonical_preview(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            paths = gui._setup_paths()
            gui._setup_write_json(paths["preview"], {"setup_id": "setup-stale"})
            gui._setup_write_json(paths["result"], {"setup_id": "setup-current"})
            gui._setup_write_json(
                paths["last_applied"],
                {
                    "setup_id": "setup-current",
                    "approved_preview_fingerprint": "sha256:preview-current",
                    "active_profile_fingerprint": "sha256:active-current",
                    "applied_at": "2026-04-09T00:00:00+00:00",
                    "restart_required": True,
                    "executor": "Codex",
                },
            )

            PipelineGUI._setup_cleanup_staged_files_once_on_startup(gui)

            self.assertIsNone(read_json(paths["preview"]))
            self.assertIsNotNone(read_json(paths["result"]))
            self.assertEqual(gui._setup_cleanup_summary_var.get(), "초기 정리: 오래된 setup 파일 1개 정리")

    def test_setup_startup_cleanup_removes_unreadable_canonical_preview(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            paths = gui._setup_paths()
            paths["preview"].parent.mkdir(parents=True, exist_ok=True)
            paths["preview"].write_text("{", encoding="utf-8")

            PipelineGUI._setup_cleanup_staged_files_once_on_startup(gui)

            self.assertFalse(paths["preview"].exists())
            self.assertEqual(gui._setup_cleanup_summary_var.get(), "초기 정리: 오래된 setup 파일 1개 정리")

    def test_setup_cleanup_keeps_current_preview_and_result_when_request_apply_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            _update_setup_state(gui, current_setup_id="setup-current")
            paths = gui._setup_paths()
            gui._setup_write_json(paths["preview"], {"setup_id": "setup-current"})
            gui._setup_write_json(paths["result"], {"setup_id": "setup-current"})

            removed = PipelineGUI._setup_cleanup_staged_files(
                gui,
                request_payload=None,
                preview_payload=read_json(paths["preview"]),
                apply_payload=None,
                result_payload=read_json(paths["result"]),
                last_applied_payload=None,
            )

            self.assertEqual(removed, [])
            self.assertTrue(paths["preview"].exists())
            self.assertTrue(paths["result"].exists())

    def test_setup_manual_clean_removes_old_staged_files_and_toasts_count(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(
                preview_delay_sec=0.01,
                result_delay_sec=0.01,
                staged_retention_sec=0.01,
            )
            paths = gui._setup_paths()
            stale_path = paths["preview"].with_name("preview.setup-old.staged.json")
            gui._setup_write_json(stale_path, {"setup_id": "setup-old"})
            time.sleep(0.02)

            PipelineGUI._on_setup_clean_staged(gui)

            self.assertFalse(stale_path.exists())
            self.assertEqual(gui.msg_var.get(), "오래된 setup 파일 1개를 정리했습니다")
            self.assertEqual(gui._setup_cleanup_summary_var.get(), "수동 정리: 오래된 setup 파일 1개 정리")

            PipelineGUI._on_setup_clean_staged(gui)

            self.assertEqual(
                gui._setup_cleanup_summary_var.get(),
                "수동 정리: 정리할 오래된 setup 파일이 없습니다\n수동 정리: 오래된 setup 파일 1개 정리",
            )

    def test_setup_manual_clean_keeps_inflight_setup_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(
                preview_delay_sec=0.01,
                result_delay_sec=0.01,
                staged_retention_sec=0.01,
            )
            _update_setup_state(gui, mode_state="PreviewWaiting", current_setup_id="setup-current")
            paths = gui._setup_paths()
            keep_path = paths["preview"].with_name("preview.setup-current.staged.json")
            stale_path = paths["preview"].with_name("preview.setup-old.staged.json")
            gui._setup_write_json(paths["request"], {"setup_id": "setup-current"})
            gui._setup_write_json(keep_path, {"setup_id": "setup-current"})
            gui._setup_write_json(stale_path, {"setup_id": "setup-old"})
            time.sleep(0.02)

            PipelineGUI._on_setup_clean_staged(gui)

            self.assertTrue(keep_path.exists())
            self.assertFalse(stale_path.exists())

    def test_stale_preview_overwrite_never_downgrades_current_preview_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()

            current_state = _setup_state(gui)
            current_setup_id = current_state.current_setup_id
            current_preview_fingerprint = current_state.current_preview_fingerprint
            gui._setup_write_json(
                gui._setup_paths()["preview"],
                {
                    "status": "preview_ready",
                    "setup_id": "setup-stale",
                    "draft_fingerprint": "sha256:stale",
                    "preview_fingerprint": "sha256:stale-preview",
                },
            )
            gui._refresh_setup_mode_state()

            self.assertEqual(_setup_state(gui).mode_state, "PreviewReady")
            self.assertEqual(_setup_state(gui).current_setup_id, current_setup_id)
            self.assertEqual(_setup_state(gui).current_preview_fingerprint, current_preview_fingerprint)

    def test_stale_result_overwrite_never_downgrades_applied_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()
            PipelineGUI._on_setup_apply(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["result"]) is not None))
            gui._refresh_setup_mode_state()

            current_state = _setup_state(gui)
            current_setup_id = current_state.current_setup_id
            current_preview_fingerprint = current_state.current_preview_fingerprint
            self.assertEqual(_setup_state(gui).mode_state, "Applied")

            gui._setup_write_json(
                gui._setup_paths()["result"],
                {
                    "status": "apply_failed",
                    "setup_id": "setup-stale",
                    "approved_preview_fingerprint": "sha256:stale",
                    "message": "stale result should not win",
                },
            )
            gui._refresh_setup_mode_state()

            self.assertEqual(_setup_state(gui).mode_state, "Applied")
            self.assertEqual(_setup_state(gui).current_setup_id, current_setup_id)
            self.assertEqual(_setup_state(gui).current_preview_fingerprint, current_preview_fingerprint)

    def test_setup_apply_holds_active_promotion_when_draft_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()
            gui._setup_paths()["draft"].unlink()

            PipelineGUI._on_setup_apply(gui)
            self.assertEqual(_setup_state(gui).mode_state, "ApplyPending")
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["result"]) is not None))
            gui._refresh_setup_mode_state()

            self.assertEqual(_setup_state(gui).mode_state, "ApplyFailed")
            self.assertIn("draft 파일이 없어", gui._setup_validation_var.get())
            self.assertIsNone(read_json(gui._setup_paths()["active"]))

    def test_setup_apply_failed_result_surfaces_errors_warnings_and_message_first(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()

            apply_payload = {
                "status": "apply_requested",
                "setup_id": _setup_state(gui).current_setup_id,
                "schema_version": 1,
                "approved_at": "2026-04-08T00:00:00Z",
                "approved_preview_fingerprint": _setup_state(gui).current_preview_fingerprint,
                "executor": "Codex",
            }
            gui._setup_write_json(gui._setup_paths()["apply"], apply_payload)
            gui._setup_write_json(
                gui._setup_paths()["result"],
                {
                    "status": "apply_failed",
                    "setup_id": _setup_state(gui).current_setup_id,
                    "approved_preview_fingerprint": _setup_state(gui).current_preview_fingerprint,
                    "errors": ["preview materialization failed"],
                    "warnings": ["manual review recommended"],
                    "message": "executor apply failed",
                },
            )
            gui._refresh_setup_mode_state()

            lines = gui._setup_validation_var.get().splitlines()
            self.assertGreaterEqual(len(lines), 3)
            self.assertEqual(lines[0], "오류: preview materialization failed")
            self.assertEqual(lines[1], "오류: executor apply failed")
            self.assertEqual(lines[2], "경고: manual review recommended")

    def test_fault_injecting_setup_executor_exercises_apply_failed_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            adapter = FaultInjectingSetupExecutorAdapter(
                preview_delay_sec=0.01,
                result_delay_sec=0.01,
                result_patch={
                    "status": "apply_failed",
                    "errors": ["simulated apply failure"],
                    "warnings": ["operator review recommended"],
                    "message": "fault injection apply failed",
                },
            )
            gui = _make_setup_gui(Path(td), adapter=adapter)

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()

            PipelineGUI._on_setup_apply(gui)
            self.assertEqual(_setup_state(gui).mode_state, "ApplyPending")
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["result"]) is not None))
            gui._refresh_setup_mode_state()

            self.assertEqual(_setup_state(gui).mode_state, "ApplyFailed")
            lines = gui._setup_validation_var.get().splitlines()
            self.assertGreaterEqual(len(lines), 3)
            self.assertEqual(lines[0], "오류: simulated apply failure")
            self.assertEqual(lines[1], "오류: fault injection apply failed")
            self.assertEqual(lines[2], "경고: operator review recommended")

    def test_setup_restart_confirmation_calls_restart_only_when_accepted(self) -> None:
        gui = _make_setup_gui(Path("/tmp/projecth-setup-test"))
        _update_setup_state(gui, mode_state="Applied", restart_required=True)
        gui._ask_yn.return_value = False

        PipelineGUI._on_setup_confirm_restart(gui)
        gui._on_restart.assert_not_called()

        gui._ask_yn.return_value = True
        PipelineGUI._on_setup_confirm_restart(gui)
        gui._on_restart.assert_called_once_with()

    def test_ask_yn_calls_messagebox_directly_on_main_thread(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.root = mock.Mock()
        with mock.patch("pipeline_gui.app.messagebox.askyesno", return_value=True) as ask_mock:
            result = PipelineGUI._ask_yn(gui, "Title", "Body", icon="question")
        self.assertTrue(result)
        ask_mock.assert_called_once_with("Title", "Body", icon="question")
        gui.root.after.assert_not_called()

    def test_start_token_maintenance_action_uses_shared_setup_flow(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._action_in_progress = False
        gui._ask_yn = mock.Mock(return_value=True)
        gui._lock_buttons = mock.Mock()
        gui._update_token_action_progress = mock.Mock()
        gui._start_token_ui_pump = mock.Mock()
        gui._token_action_initial_payload = mock.Mock(return_value={"phase": "preparing"})
        worker = mock.Mock()

        with mock.patch("pipeline_gui.app.threading.Thread") as thread_cls:
            thread = thread_cls.return_value
            PipelineGUI._start_token_maintenance_action(
                gui,
                action_label="전체 히스토리",
                dialog_title="Title",
                dialog_message="Body",
                icon="question",
                lock_message="LOCK",
                worker_target=worker,
            )

        gui._ask_yn.assert_called_once_with("Title", "Body", icon="question")
        gui._lock_buttons.assert_called_once_with("LOCK")
        gui._update_token_action_progress.assert_called_once_with("전체 히스토리", {"phase": "preparing"})
        gui._start_token_ui_pump.assert_called_once_with()
        thread_cls.assert_called_once_with(target=worker, daemon=True)
        thread.start.assert_called_once_with()

    def test_run_token_maintenance_action_enqueues_shared_success_flow(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        queued: list[object] = []
        gui._enqueue_token_ui = lambda callback: queued.append(callback)
        gui._format_token_action_done = mock.Mock(return_value="작업: 완료")
        gui._set_token_action_text = mock.Mock()
        gui._refresh_token_dashboard_async = mock.Mock()
        gui._start_token_usage_refresh = mock.Mock()
        gui._unlock_buttons = mock.Mock()
        gui._clear_msg_later = mock.Mock()

        PipelineGUI._run_token_maintenance_action(
            gui,
            action_label="DB 재구성",
            action_runner=lambda: {
                "summary": {"elapsed_sec": 3.2, "usage_inserted": 12},
                "backup_path": "/tmp/usage.backup-1.db",
            },
            unlock_message_builder=lambda summary, backup_path: (
                f"done {summary['elapsed_sec']:.1f} {backup_path}"
            ),
            error_message="should not be used",
        )

        for callback in queued:
            callback()

        gui._format_token_action_done.assert_called_once()
        gui._set_token_action_text.assert_called_once_with("작업: 완료")
        gui._refresh_token_dashboard_async.assert_called_once_with()
        gui._start_token_usage_refresh.assert_called_once_with(force=True)
        gui._unlock_buttons.assert_called_once_with("done 3.2 /tmp/usage.backup-1.db")
        gui._clear_msg_later.assert_called_once_with(10000)

    def test_set_main_button_states_handles_disabled_and_ready_modes(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.btn_setup = _Widget()
        gui.btn_start = _Widget()
        gui.btn_stop = _Widget()
        gui.btn_restart = _Widget()
        gui.btn_attach = _Widget()
        gui.btn_token_backfill = _Widget()
        gui.btn_token_rebuild = _Widget()

        PipelineGUI._set_main_button_states(gui, all_disabled=True)
        self.assertEqual(gui.btn_setup.state, "disabled")
        self.assertEqual(gui.btn_start.state, "disabled")
        self.assertEqual(gui.btn_token_rebuild.state, "disabled")

        PipelineGUI._set_main_button_states(gui, all_disabled=False, can_start=True, session_ok=True)
        self.assertEqual(gui.btn_setup.state, "normal")
        self.assertEqual(gui.btn_start.state, "normal")
        self.assertEqual(gui.btn_stop.state, "normal")
        self.assertEqual(gui.btn_restart.state, "normal")
        self.assertEqual(gui.btn_attach.state, "normal")
        self.assertEqual(gui.btn_token_backfill.state, "normal")
        self.assertEqual(gui.btn_token_rebuild.state, "normal")

    def test_sync_start_button_state_blocks_launch_for_blocked_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_state = "ready"
            gui._last_snapshot = {"session_ok": False}
            blocked_active = gui._setup_active_payload(
                gui._setup_draft_payload(
                    {
                        "schema_version": 1,
                        "selected_agents": ["Codex"],
                        "role_bindings": {"implement": "Codex", "verify": "Codex", "advisory": ""},
                        "role_options": {"advisory_enabled": False, "operator_stop_enabled": True, "session_arbitration_enabled": False},
                        "mode_flags": {"single_agent_mode": True, "self_verify_allowed": False, "self_advisory_allowed": False},
                        "executor_override": "auto",
                    }
                ),
                source_setup_id="setup-blocked",
            )
            gui._setup_write_json(gui._setup_paths()["active"], blocked_active)

            PipelineGUI._sync_start_button_state(gui)

            self.assertEqual(gui.btn_start.state, "disabled")
            self.assertEqual(gui.btn_restart.state, "disabled")
            self.assertIn("실행 차단", gui.setup_var.get())
            self.assertIn("실행 프로필: 차단", gui._runtime_launch_var.get())
            self.assertIn("implement and verify cannot share", gui._runtime_launch_var.get())

    def test_sync_start_button_state_blocks_launch_for_missing_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_state = "ready"
            gui._last_snapshot = {"session_ok": False}

            PipelineGUI._sync_start_button_state(gui)

            self.assertEqual(gui.btn_start.state, "disabled")
            self.assertEqual(gui.btn_restart.state, "disabled")
            self.assertIn("실행 차단", gui.setup_var.get())
            self.assertIn("active profile이 없습니다", gui.setup_var.get())
            self.assertEqual(gui.setup_state_label._fg, "#ef4444")
            self.assertIn("실행 프로필: 차단", gui._runtime_launch_var.get())
            self.assertIn("실행 프로필: 차단", gui._setup_runtime_profile_var.get())
            self.assertIn("active profile이 없습니다", gui._runtime_launch_var.get())

    def test_sync_start_button_state_keeps_ready_setup_state_for_supported_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_state = "ready"
            gui._last_snapshot = {"session_ok": False}
            supported_active = gui._setup_active_payload(
                gui._setup_draft_payload(
                    {
                        "schema_version": 1,
                        "selected_agents": ["Claude", "Codex", "Gemini"],
                        "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
                        "role_options": {"advisory_enabled": True, "operator_stop_enabled": True, "session_arbitration_enabled": True},
                        "mode_flags": {"single_agent_mode": False, "self_verify_allowed": False, "self_advisory_allowed": False},
                        "executor_override": "auto",
                    }
                ),
                source_setup_id="setup-supported",
            )
            gui._setup_write_json(gui._setup_paths()["active"], supported_active)

            PipelineGUI._sync_start_button_state(gui)

            self.assertEqual(gui.btn_start.state, "normal")
            self.assertEqual(gui.setup_var.get(), "설정: ● 준비됨")
            self.assertEqual(gui.setup_state_label._fg, "#34d399")
            self.assertIn("실행 프로필: 지원", gui._setup_runtime_profile_var.get())

    def test_sync_start_button_state_allows_experimental_launch_with_notice(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_state = "ready_warn"
            gui._last_snapshot = {"session_ok": False}
            experimental_active = gui._setup_active_payload(
                gui._setup_draft_payload(
                    {
                        "schema_version": 1,
                        "selected_agents": ["Codex"],
                        "role_bindings": {"implement": "Codex", "verify": "Codex", "advisory": ""},
                        "role_options": {"advisory_enabled": False, "operator_stop_enabled": True, "session_arbitration_enabled": False},
                        "mode_flags": {"single_agent_mode": True, "self_verify_allowed": True, "self_advisory_allowed": False},
                        "executor_override": "auto",
                    }
                ),
                source_setup_id="setup-experimental",
            )
            gui._setup_write_json(gui._setup_paths()["active"], experimental_active)

            PipelineGUI._sync_start_button_state(gui)

            self.assertEqual(gui.btn_start.state, "normal")
            self.assertEqual(gui._runtime_launch_label._fg, "#fbbf24")
            self.assertIn("실행 프로필: 실험적", gui._runtime_launch_var.get())
            self.assertIn("extra operator attention", gui._runtime_launch_var.get())

    def test_on_start_surfaces_blocked_profile_messages_without_launching(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_state = "ready"
            blocked_active = gui._setup_active_payload(
                gui._setup_draft_payload(
                    {
                        "schema_version": 1,
                        "selected_agents": ["Codex"],
                        "role_bindings": {"implement": "Codex", "verify": "Codex", "advisory": ""},
                        "role_options": {"advisory_enabled": False, "operator_stop_enabled": True, "session_arbitration_enabled": False},
                        "mode_flags": {"single_agent_mode": True, "self_verify_allowed": False, "self_advisory_allowed": False},
                        "executor_override": "auto",
                    }
                ),
                source_setup_id="setup-blocked",
            )
            gui._setup_write_json(gui._setup_paths()["active"], blocked_active)

            PipelineGUI._on_start(gui)

            gui._lock_buttons.assert_not_called()
            self.assertIn("implement and verify cannot share", gui.msg_var.get())

    def test_on_start_surfaces_missing_active_profile_message_without_launching(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_state = "ready"

            PipelineGUI._on_start(gui)

            gui._lock_buttons.assert_not_called()
            self.assertIn("active profile이 없습니다", gui.msg_var.get())
            self.assertIn(".pipeline/config/agent_profile.json", gui.msg_var.get())

    def test_on_restart_surfaces_blocked_profile_messages_without_stopping(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_state = "ready"
            blocked_active = gui._setup_active_payload(
                gui._setup_draft_payload(
                    {
                        "schema_version": 1,
                        "selected_agents": ["Codex"],
                        "role_bindings": {"implement": "Codex", "verify": "Codex", "advisory": ""},
                        "role_options": {"advisory_enabled": False, "operator_stop_enabled": True, "session_arbitration_enabled": False},
                        "mode_flags": {"single_agent_mode": True, "self_verify_allowed": False, "self_advisory_allowed": False},
                        "executor_override": "auto",
                    }
                ),
                source_setup_id="setup-blocked",
            )
            gui._setup_write_json(gui._setup_paths()["active"], blocked_active)

            PipelineGUI._on_restart(gui)

            gui._lock_buttons.assert_not_called()
            self.assertIn("implement and verify cannot share", gui.msg_var.get())

    def test_poll_status_text_marks_live_snapshot_fresh_and_stale(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._last_poll_at = 100.0

        text, color = PipelineGUI._poll_status_text(gui, is_live=True, now=101.0)
        self.assertEqual(text, "폴링: 최신 1초")
        self.assertEqual(color, "#34d399")

        text, color = PipelineGUI._poll_status_text(gui, is_live=True, now=105.0)
        self.assertEqual(text, "폴링: 지연 5초")
        self.assertEqual(color, "#e0a040")

    def test_poll_status_text_marks_last_run_when_not_live(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._last_poll_at = 100.0

        text, color = PipelineGUI._poll_status_text(gui, is_live=False, now=104.0)
        self.assertEqual(text, "폴링: 마지막 실행 4초 전")
        self.assertEqual(color, "#666666")

    def test_token_dashboard_loading_prefers_home_controller_state(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._action_in_progress = False
        gui._token_action_var = _Var("")
        controller = mock.Mock()
        controller.token_dashboard_loading.return_value = True
        gui._home_controller = controller

        self.assertTrue(PipelineGUI._token_dashboard_loading(gui))
        controller.token_dashboard_loading.assert_called_once_with()

    def test_resolve_runtime_active_profile_delegates_to_setup_controller(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        controller = mock.Mock()
        controller.resolve_runtime_active_profile.return_value = {
            "support_level": "supported",
            "controls": {"launch_allowed": True},
        }
        gui._ensure_setup_controller = mock.Mock(return_value=controller)
        gui._setup_controller = controller
        gui._export_setup_state = mock.Mock(return_value=SetupActionState())
        gui._apply_setup_state_model = mock.Mock()

        first = PipelineGUI._resolve_runtime_active_profile(gui)
        second = PipelineGUI._resolve_runtime_active_profile(gui)

        self.assertEqual(first, second)
        self.assertEqual(controller.resolve_runtime_active_profile.call_count, 2)

    def test_read_setup_disk_state_delegates_to_setup_controller(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        controller = mock.Mock()
        controller.read_disk_state.return_value = {"active_exists": False}
        gui._ensure_setup_controller = mock.Mock(return_value=controller)
        gui._setup_controller = controller

        first = PipelineGUI._read_setup_disk_state(gui)
        second = PipelineGUI._read_setup_disk_state(gui)

        self.assertEqual(first, {"active_exists": False})
        self.assertEqual(second, {"active_exists": False})
        self.assertEqual(controller.read_disk_state.call_count, 2)

    def test_refresh_setup_mode_state_if_due_skips_when_not_in_setup_mode(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._mode = "home"
        gui._setup_snapshot_refresh_last_at = 0.0
        gui._setup_snapshot_refresh_ttl_sec = 2.0
        gui._apply_setup_fast_snapshot = mock.Mock()
        gui._build_setup_fast_snapshot = mock.Mock(return_value={})
        gui._schedule_setup_detail_refresh = mock.Mock()

        PipelineGUI._refresh_setup_mode_state_if_due(gui)

        gui._apply_setup_fast_snapshot.assert_not_called()
        gui._schedule_setup_detail_refresh.assert_not_called()

    def test_refresh_setup_mode_state_if_due_runs_fast_and_schedules_detail_when_setup_mode_cache_is_stale(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._mode = "setup"
        gui._setup_snapshot_refresh_last_at = 0.0
        gui._setup_snapshot_refresh_ttl_sec = 30.0
        gui._setup_refresh_after_id = None
        gui._setup_detail_after_id = None
        gui._setup_refresh_generation = 0
        gui._apply_setup_fast_snapshot = mock.Mock()
        gui._build_setup_fast_snapshot = mock.Mock(return_value={"fast": True})
        gui._schedule_setup_detail_refresh = mock.Mock()
        gui._invalidate_setup_refresh_generation = PipelineGUI._invalidate_setup_refresh_generation.__get__(gui, PipelineGUI)
        gui._cancel_setup_refresh_callbacks = PipelineGUI._cancel_setup_refresh_callbacks.__get__(gui, PipelineGUI)

        with mock.patch("pipeline_gui.app.time.time", return_value=100.0):
            PipelineGUI._refresh_setup_mode_state_if_due(gui)

        gui._build_setup_fast_snapshot.assert_called_once_with()
        gui._apply_setup_fast_snapshot.assert_called_once_with({"fast": True})
        gui._schedule_setup_detail_refresh.assert_called_once_with(
            1,
            delay_ms=0,
            after_idle=True,
        )

    def test_setup_write_json_invalidates_setup_and_runtime_caches(self) -> None:
        gui = _make_setup_gui(Path("/tmp/projectH"))
        _update_setup_state(gui, runtime_launch_resolution={"support_level": "supported"})
        path = Path("/tmp/projectH/.pipeline/config/agent_profile.json")

        with mock.patch.object(gui._setup_controller, "write_json") as write_json, mock.patch.object(
            gui._setup_controller, "invalidate_runtime_caches"
        ) as invalidate_runtime_caches:
            PipelineGUI._setup_write_json(gui, path, {"schema_version": 1})

        write_json.assert_called_once_with(path, {"schema_version": 1})
        invalidate_runtime_caches.assert_called_once_with()
        self.assertIsNone(_setup_state(gui).runtime_launch_resolution)

    def test_request_setup_mode_refresh_coalesces_fast_and_detail_callbacks(self) -> None:
        gui = _make_setup_gui(Path("/tmp/projectH"))
        gui._mode = "setup"
        gui.root = _FakeRoot()
        gui._build_setup_fast_snapshot = mock.Mock(return_value={"fast": True})
        gui._apply_setup_fast_snapshot = mock.Mock()
        gui._run_setup_detail_refresh = mock.Mock()

        PipelineGUI._request_setup_mode_refresh(gui)
        first_fast = gui._setup_refresh_after_id
        first_detail = gui._setup_detail_after_id

        PipelineGUI._request_setup_mode_refresh(gui)
        second_fast = gui._setup_refresh_after_id
        second_detail = gui._setup_detail_after_id

        self.assertNotEqual(first_fast, second_fast)
        self.assertNotEqual(first_detail, second_detail)
        self.assertIn(first_fast, gui.root.cancelled)
        self.assertIn(first_detail, gui.root.cancelled)

        gui.root.run(second_fast)
        gui._apply_setup_fast_snapshot.assert_called_once_with({"fast": True})
        gui.root.run(second_detail)
        gui._run_setup_detail_refresh.assert_called_once_with(gui._setup_refresh_generation)

    def test_run_setup_detail_refresh_skips_when_mode_is_not_setup(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._mode = "home"
        gui._setup_refresh_generation = 3
        gui._build_setup_detail_snapshot = mock.Mock(return_value={})
        gui._apply_setup_detail_snapshot = mock.Mock()

        PipelineGUI._run_setup_detail_refresh(gui, 3)

        gui._build_setup_detail_snapshot.assert_not_called()
        gui._apply_setup_detail_snapshot.assert_not_called()

    def test_run_setup_detail_refresh_ignores_stale_generation(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._mode = "setup"
        gui._setup_refresh_generation = 4
        gui._build_setup_detail_snapshot = mock.Mock(return_value={})
        gui._apply_setup_detail_snapshot = mock.Mock()

        PipelineGUI._run_setup_detail_refresh(gui, 3)

        gui._build_setup_detail_snapshot.assert_not_called()
        gui._apply_setup_detail_snapshot.assert_not_called()

    def test_switch_mode_setup_runs_fast_now_and_schedules_detail_after_idle(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._mode = "home"
        gui.root = _FakeRoot()
        gui._setup_refresh_after_id = None
        gui._setup_detail_after_id = None
        gui._setup_refresh_generation = 0
        gui._cancel_setup_refresh_callbacks = PipelineGUI._cancel_setup_refresh_callbacks.__get__(gui, PipelineGUI)
        gui._invalidate_setup_refresh_generation = PipelineGUI._invalidate_setup_refresh_generation.__get__(gui, PipelineGUI)
        gui._build_setup_fast_snapshot = mock.Mock(return_value={"fast": True})
        gui._apply_setup_fast_snapshot = mock.Mock()
        gui._schedule_setup_detail_refresh = mock.Mock()
        gui._home_frame = _Widget()
        gui._guide_frame = _Widget()
        gui._setup_frame = _Widget()
        gui._mode_btn_home = _Widget()
        gui._mode_btn_guide = _Widget()
        gui._mode_btn_setup = _Widget()

        PipelineGUI._switch_mode(gui, "setup")

        gui._apply_setup_fast_snapshot.assert_called_once_with({"fast": True})
        gui._schedule_setup_detail_refresh.assert_called_once_with(
            1,
            delay_ms=0,
            after_idle=True,
        )

    def test_update_setup_action_buttons_stays_fail_closed_before_detail_ready(self) -> None:
        gui = _make_setup_gui(Path("/tmp/projectH"))
        _update_setup_state(
            gui,
            mode_state="PreviewReady",
            detail_ready=False,
            current_preview_payload={"controls": {"apply_allowed": True}},
            current_support_resolution={"controls": {"preview_allowed": True}},
            dirty=False,
            draft_saved=True,
        )

        PipelineGUI._update_setup_action_buttons(gui)
        self.assertEqual(gui.btn_setup_apply.state, "disabled")

        _update_setup_state(gui, detail_ready=True)
        PipelineGUI._update_setup_action_buttons(gui)
        self.assertEqual(gui.btn_setup_apply.state, "normal")

    def test_schedule_refresh_setup_mode_state_runs_cleanup_only_on_roundtrip_completion(self) -> None:
        gui = _make_setup_gui(Path("/tmp/projectH"))
        gui._mode = "setup"
        gui.root = _FakeRoot()
        gui._build_setup_fast_snapshot = mock.Mock(return_value={"fast": True})
        gui._apply_setup_fast_snapshot = mock.Mock()
        gui._setup_run_automatic_cleanup = mock.Mock()
        gui._schedule_setup_detail_refresh = mock.Mock()
        gui._invalidate_setup_refresh_generation = PipelineGUI._invalidate_setup_refresh_generation.__get__(gui, PipelineGUI)
        gui._cancel_setup_refresh_callbacks = PipelineGUI._cancel_setup_refresh_callbacks.__get__(gui, PipelineGUI)

        PipelineGUI._schedule_refresh_setup_mode_state(gui, run_cleanup=True)
        gui.root.run_all()

        gui._setup_run_automatic_cleanup.assert_called_once_with()
        gui._apply_setup_fast_snapshot.assert_called_once_with({"fast": True})
        gui._schedule_setup_detail_refresh.assert_called_once_with(
            1,
            delay_ms=0,
            after_idle=True,
        )

    def test_schedule_refresh_setup_mode_state_refreshes_detail_in_home_mode(self) -> None:
        gui = _make_setup_gui(Path("/tmp/projectH"))
        gui._mode = "home"
        gui.root = _FakeRoot()
        gui._build_setup_fast_snapshot = mock.Mock(return_value={"fast": True})
        gui._apply_setup_fast_snapshot = mock.Mock()
        gui._setup_run_automatic_cleanup = mock.Mock()
        gui._refresh_setup_mode_state = mock.Mock()
        gui._schedule_setup_detail_refresh = mock.Mock()
        gui._invalidate_setup_refresh_generation = PipelineGUI._invalidate_setup_refresh_generation.__get__(gui, PipelineGUI)
        gui._cancel_setup_refresh_callbacks = PipelineGUI._cancel_setup_refresh_callbacks.__get__(gui, PipelineGUI)

        PipelineGUI._schedule_refresh_setup_mode_state(gui, run_cleanup=True)
        gui.root.run_all()

        gui._setup_run_automatic_cleanup.assert_called_once_with()
        gui._refresh_setup_mode_state.assert_called_once_with()
        gui._apply_setup_fast_snapshot.assert_not_called()
        gui._schedule_setup_detail_refresh.assert_not_called()

if __name__ == "__main__":
    unittest.main()
