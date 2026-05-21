# Pipeline Launcher Bugfix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 파이프라인 런처 코드 분석에서 발견된 18개 문제(P1–P18)를 버그 수정, 로직 교정, 성능 개선, 구조적 안정성 순서로 4개 태스크에 걸쳐 수정한다.

**Architecture:** supervisor.py(RuntimeSupervisor), cli.py(CLI + _WrapperEmitter), automation_health.py 세 파일을 중심으로 수정하며, 각 태스크는 독립적으로 컴파일 가능하고 기존 테스트를 통과해야 한다. 각 수정 전에 실패 테스트를 작성하고 수정 후 통과를 확인하는 TDD 흐름을 유지한다.

**Tech Stack:** Python 3.12, unittest, hashlib, fcntl, tempfile, pathlib

---

## 파일 맵

| 파일 | 태스크 | 변경 내용 |
|---|---|---|
| `pipeline_runtime/supervisor.py` | 1, 2, 3, 4 | SHA 캐시 · 루프 정리 · 예외 로깅 · 원자적 쓰기 · raw.jsonl 보존 · events.jsonl 중복 억제 · post-accept 보호 · 스폰 실패 정리 |
| `pipeline_runtime/cli.py` | 1, 2 | doctor tmux 버그 · format KeyError · 하드코딩 키 · control_seq 변환 |
| `pipeline_runtime/automation_health.py` | 1 | unknown reason fallthrough 수정 |
| `tests/test_pipeline_runtime_supervisor.py` | 1, 2, 3, 4 | 각 수정에 대한 회귀 테스트 추가 |
| `tests/test_pipeline_runtime_cli.py` | 1, 2 | doctor tmux · format KeyError · auto-dismiss 개선 테스트 추가 |
| `tests/test_pipeline_runtime_automation_health.py` | 1 | unknown reason family 테스트 추가 |

---

## Task 1: 단순 버그 수정 (P6, P9, P10, P14, P15, P17)

**Files:**
- Modify: `pipeline_runtime/supervisor.py` (lines 370–373, 863–865, 1862, 1959–1965)
- Modify: `pipeline_runtime/cli.py` (lines 483–489)
- Modify: `pipeline_runtime/automation_health.py` (line 136)
- Test: `tests/test_pipeline_runtime_supervisor.py`
- Test: `tests/test_pipeline_runtime_cli.py`
- Test: `tests/test_pipeline_runtime_automation_health.py`

---

### 1-A. P9: doctor tmux 체크가 항상 "ok"를 반환하는 버그

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_pipeline_runtime_cli.py` 내 기존 `test_doctor_json_reports_ready_project_without_current_run` 클래스 아래에 추가:

```python
def test_doctor_reports_tmux_warn_when_session_missing(self) -> None:
    """tmux 세션이 없으면 tmux_session 체크가 warn을 반환해야 한다."""
    import json
    from pipeline_runtime.cli import _doctor_payload
    from unittest.mock import patch

    proj = self._project_root  # 기존 픽스처 활용
    with patch(
        "pipeline_runtime.cli.TmuxAdapter.session_exists", return_value=False
    ):
        payload = _doctor_payload(proj, "test-session")

    tmux_check = next(
        (c for c in payload["checks"] if c["name"] == "tmux_session"), None
    )
    self.assertIsNotNone(tmux_check)
    self.assertEqual(tmux_check["status"], "warn")
    self.assertIn("not found", tmux_check["detail"])
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd /home/xpdlqj/code/projectH
python3 -m unittest tests.test_pipeline_runtime_cli.DoctorPayloadTest.test_doctor_reports_tmux_warn_when_session_missing -v
```

Expected: FAIL — `AssertionError: 'ok' != 'warn'`

- [ ] **Step 3: 수정 적용 — cli.py:483–489**

```python
# Before
_doctor_check(
    "tmux_session",
    "ok" if tmux_session_exists else "ok",
    severity="advisory",
    detail=f"{session_name}: {'exists' if tmux_session_exists else 'not found'}",
)

# After
_doctor_check(
    "tmux_session",
    "ok" if tmux_session_exists else "warn",
    severity="advisory",
    detail=f"{session_name}: {'exists' if tmux_session_exists else 'not found'}",
    hint="" if tmux_session_exists else "Run: python3 -m pipeline_runtime.cli start",
)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_cli.DoctorPayloadTest.test_doctor_reports_tmux_warn_when_session_missing -v
```

Expected: PASS

---

### 1-B. P17: automation_incident_family가 알 수 없는 reason을 그대로 반환

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_pipeline_runtime_automation_health.py` 내 추가:

```python
def test_unknown_reason_code_returns_empty_family(self) -> None:
    """정의되지 않은 reason code는 빈 문자열 family를 반환해야 한다."""
    from pipeline_runtime.automation_health import automation_incident_family

    result = automation_incident_family("totally_unknown_reason_xyz")
    self.assertEqual(result, "")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_automation_health -k test_unknown_reason_code_returns_empty_family -v
```

Expected: FAIL — `AssertionError: 'totally_unknown_reason_xyz' != ''`

- [ ] **Step 3: 수정 적용 — automation_health.py line 136**

```python
# Before (automation_health.py 끝 부분)
    if reason == "lane_recovery_exhausted" or reason.endswith("_recovery_failed") or reason.endswith("_broken"):
        return "lane_recovery_exhausted"
    return reason  # ← 알 수 없는 reason 그대로 반환

# After
    if reason == "lane_recovery_exhausted" or reason.endswith("_recovery_failed") or reason.endswith("_broken"):
        return "lane_recovery_exhausted"
    return ""  # unknown reason — 빈 family 반환
```

- [ ] **Step 4: 테스트 통과 확인 + 기존 테스트 회귀 없음**

```bash
python3 -m unittest tests.test_pipeline_runtime_automation_health -v
```

Expected: 전체 PASS

---

### 1-C. P10: lane command override format KeyError 시 미해석 템플릿이 셸로 전달

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_pipeline_runtime_supervisor.py` 내 기존 `test_lane_command_override_*` 테스트들 아래에 추가:

```python
def test_lane_command_override_format_key_error_returns_empty_and_logs_event(
    self,
) -> None:
    """format 키 오류 시 빈 문자열을 반환하고 override_invalid 이벤트를 기록해야 한다."""
    import os
    from unittest.mock import patch

    env = {
        "PIPELINE_RUNTIME_ALLOW_LANE_COMMAND_OVERRIDE": "1",
        "PIPELINE_RUNTIME_LANE_COMMAND_CODEX": "exec mybin {unknown_key}",
    }
    with patch.dict(os.environ, env):
        result = self.supervisor._lane_command_override("Codex")

    self.assertEqual(result, "")
    events = self._read_events()
    override_invalid = [e for e in events if e.get("event_type") == "lane_command_override_invalid"]
    self.assertEqual(len(override_invalid), 1)
    self.assertIn("format_key_error", override_invalid[0]["payload"]["reason"])
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_lane_command_override_format_key_error -v
```

Expected: FAIL — 이벤트 미발생 또는 반환값이 비어있지 않음

- [ ] **Step 3: 수정 적용 — supervisor.py lines 370–373**

```python
# Before
        try:
            command = template.format(**context)
        except KeyError:
            command = template

# After
        try:
            command = template.format(**context)
        except KeyError as exc:
            self._append_event(
                "lane_command_override_invalid",
                {
                    "lane": lane_name,
                    "source": source,
                    "reason": f"format_key_error:{exc}",
                },
            )
            return ""
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_lane_command_override -v
```

Expected: 전체 PASS (기존 + 신규)

---

### 1-D. P14: _reconcile_receipts의 불필요한 단일 항목 루프

- [ ] **Step 1: 수정 적용 — supervisor.py line 1862**

테스트가 불필요한 단순 리팩터링이므로 기존 테스트가 통과함을 확인한 뒤 바로 수정한다.

```python
# Before
        for job_state in [latest_job]:
            job_id = str(job_state.get("job_id") or "")

# After
        job_state = latest_job
        job_id = str(job_state.get("job_id") or "")
```

이하 루프 블록의 들여쓰기를 한 레벨 줄인다 (내용 변경 없음).

- [ ] **Step 2: 컴파일 + 기존 테스트 통과 확인**

```bash
python3 -m py_compile pipeline_runtime/supervisor.py && \
python3 -m unittest tests.test_pipeline_runtime_supervisor -k receipt -v
```

Expected: PASS

---

### 1-E. P15: _refresh_control_seq_age의 광범위한 except Exception 억제

- [ ] **Step 1: 수정 적용 — supervisor.py lines 863–865**

```python
# Before
        except Exception:
            current_seq = None

# After
        except Exception as exc:
            self._append_event(
                "control_seq_age_error",
                {"error": f"{type(exc).__name__}: {exc}"},
            )
            current_seq = None
```

- [ ] **Step 2: 컴파일 확인**

```bash
python3 -m py_compile pipeline_runtime/supervisor.py && echo "OK"
```

---

### 1-F. P6: _write_compat_files의 비원자적 텍스트 파일 쓰기

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_pipeline_runtime_supervisor.py` 내 추가:

```python
def test_write_compat_files_uses_atomic_pattern_for_text_files(self) -> None:
    """latest-work.txt와 latest-verify.txt는 원자적으로 쓰여야 한다.
    즉, 최종 경로에 직접 write_text하지 않고 임시 파일을 통해 rename해야 한다."""
    import os
    status = {
        "artifacts": {
            "latest_work": {"path": "work/5/21/test.md"},
            "latest_verify": {"path": "verify/5/21/test.md"},
        },
        "compat": {"control_slots": {}},
    }
    self.supervisor.compat_dir.mkdir(parents=True, exist_ok=True)

    writes: list[str] = []
    original_write_text = pathlib.Path.write_text

    def tracking_write_text(self_path, *args, **kwargs):
        writes.append(str(self_path))
        return original_write_text(self_path, *args, **kwargs)

    import pathlib
    with unittest.mock.patch.object(pathlib.Path, "write_text", tracking_write_text):
        self.supervisor._write_compat_files(status)

    # latest-work.txt와 latest-verify.txt는 직접 write_text로 쓰이지 않아야 한다
    for w in writes:
        self.assertNotIn("latest-work.txt", w, "latest-work.txt should not be written directly")
        self.assertNotIn("latest-verify.txt", w, "latest-verify.txt should not be written directly")

    # 내용은 올바르게 쓰여야 한다
    work_path = self.supervisor.compat_dir / "latest-work.txt"
    verify_path = self.supervisor.compat_dir / "latest-verify.txt"
    self.assertEqual(work_path.read_text(), "work/5/21/test.md")
    self.assertEqual(verify_path.read_text(), "verify/5/21/test.md")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_write_compat_files_uses_atomic -v
```

Expected: FAIL

- [ ] **Step 3: 수정 적용 — supervisor.py lines 1959–1965**

```python
# Before
        (self.compat_dir / "latest-work.txt").write_text(
            str(((status.get("artifacts") or {}).get("latest_work") or {}).get("path") or "—"),
            encoding="utf-8",
        )
        (self.compat_dir / "latest-verify.txt").write_text(
            str(((status.get("artifacts") or {}).get("latest_verify") or {}).get("path") or "—"),
            encoding="utf-8",
        )

# After
        import tempfile as _tempfile
        for fname, value in [
            (
                "latest-work.txt",
                str(((status.get("artifacts") or {}).get("latest_work") or {}).get("path") or "—"),
            ),
            (
                "latest-verify.txt",
                str(((status.get("artifacts") or {}).get("latest_verify") or {}).get("path") or "—"),
            ),
        ]:
            target = self.compat_dir / fname
            try:
                fd, tmp = _tempfile.mkstemp(dir=self.compat_dir, prefix=f".{fname}.")
                try:
                    os.write(fd, value.encode("utf-8"))
                finally:
                    os.close(fd)
                os.replace(tmp, target)
            except OSError:
                pass
```

> 참고: `import tempfile as _tempfile`은 파일 맨 위 import 블록에 추가하거나, 이미 있으면 생략한다.

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_write_compat_files -v
```

Expected: PASS

- [ ] **Step 5: 전체 Task 1 검증 및 커밋**

```bash
python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/cli.py pipeline_runtime/automation_health.py
python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_automation_health -v 2>&1 | tail -20
```

Expected: 전체 PASS, 신규 테스트 포함

```bash
git add pipeline_runtime/supervisor.py pipeline_runtime/cli.py pipeline_runtime/automation_health.py \
        tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_cli.py \
        tests/test_pipeline_runtime_automation_health.py
git commit -m "fix(launcher): P6/P9/P10/P14/P15/P17 simple bug fixes

- doctor tmux check: always-ok → 'warn' when session missing (P9)
- automation_incident_family: unknown reason → '' instead of passthrough (P17)
- lane_command_override: KeyError → log event and return '' (P10)
- _reconcile_receipts: remove pointless single-item loop (P14)
- _refresh_control_seq_age: log exception instead of silent swallow (P15)
- _write_compat_files: atomic temp+rename for latest-work/verify txt (P6)"
```

---

## Task 2: 로직 교정 (P8, P11, P13, P16, P18)

**Files:**
- Modify: `pipeline_runtime/supervisor.py` (lines 1935–1938, 2878–2906, 2580–2590)
- Modify: `pipeline_runtime/cli.py` (lines 962–964, 1120–1133)
- Test: `tests/test_pipeline_runtime_supervisor.py`
- Test: `tests/test_pipeline_runtime_cli.py`

---

### 2-A. P11: verify/advisory 레인이 post-accept 상태에서 재시작될 수 있음

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_pipeline_runtime_supervisor.py` 내 추가:

```python
def test_maybe_recover_lane_blocks_verify_restart_post_accept(self) -> None:
    """verify 레인이 작업을 수락한 상태(post_accept)면 재시작 없이 terminal reason을 반환해야 한다."""
    lane = {"name": "Codex", "state": "BROKEN"}
    lane_model = {
        "accepted_task": {"job_id": "job-001", "dispatch_id": "d-001"},
        "state": "BROKEN",
    }
    # verify_owner가 "Codex"인 픽스처 기준
    result = self.supervisor._maybe_recover_lane(
        lane,
        lane_model=lane_model,
        active_round={"state": "VERIFYING", "job_id": "job-001"},
    )
    self.assertIn("interrupted_post_accept", result)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_maybe_recover_lane_blocks_verify_restart_post_accept -v
```

Expected: FAIL (재시작 시도 후 `""` 또는 다른 이유 반환)

- [ ] **Step 3: 수정 적용 — supervisor.py lines 1935–1938**

```python
# Before
        if lane_name == implement_owner and post_accept:
            return f"{lane_name.lower()}_interrupted_post_accept"

# After
        if post_accept:
            return f"{lane_name.lower()}_interrupted_post_accept"
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k recover_lane -v
```

Expected: 전체 PASS (기존 implement 보호 + 신규 verify/advisory 보호)

---

### 2-B. P8: 레인 스폰 실패 시 이미 스폰된 레인이 정리되지 않음

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_pipeline_runtime_supervisor.py` 내 추가:

```python
def test_spawn_runtime_session_cleans_up_on_lane_failure(self) -> None:
    """두 번째 레인 스폰이 실패하면 첫 번째 레인도 kill 되어야 한다."""
    from unittest.mock import call, patch

    spawned: list[str] = []
    killed: list[str] = []

    def fake_spawn_lane(lane_name: str, command: str) -> bool:
        spawned.append(lane_name)
        return len(spawned) < 2  # 두 번째에서 실패

    def fake_kill_lane(lane_name: str) -> None:
        killed.append(lane_name)

    with (
        patch.object(self.supervisor.adapter, "create_scaffold"),
        patch.object(self.supervisor.adapter, "spawn_lane", side_effect=fake_spawn_lane),
        patch.object(self.supervisor.adapter, "kill_lane", side_effect=fake_kill_lane),
        patch.object(self.supervisor, "_spawn_experimental_watcher"),
        patch.object(self.supervisor, "_start_token_collector"),
    ):
        with self.assertRaises(RuntimeError):
            self.supervisor._spawn_runtime_session()

    # 실패 전 스폰된 레인이 kill 되어야 한다
    self.assertGreater(len(killed), 0, "Failed spawn should trigger cleanup of earlier lanes")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_spawn_runtime_session_cleans_up -v
```

Expected: FAIL — `killed` 리스트가 비어있음

- [ ] **Step 3: 수정 적용 — supervisor.py lines 2878–2906**

```python
    def _spawn_runtime_session(self) -> None:
        self.adapter.create_scaffold()

        lane_configs = self.runtime_lane_configs or build_lane_configs(
            enabled_lanes=self.enabled_lanes,
            role_owners=self.role_owners,
        )
        spawned_lanes: list[str] = []
        try:
            for lane_cfg in lane_configs:
                lane_name = str(lane_cfg.get("name") or "").strip()
                if not lane_name:
                    continue
                enabled = bool(lane_cfg.get("enabled", lane_name in self.enabled_lanes))
                command = (
                    self._lane_shell_command(lane_name)
                    if enabled
                    else self._disabled_lane_command(lane_name)
                )
                if not self.adapter.spawn_lane(lane_name, command):
                    raise RuntimeError(f"lane spawn failed: {lane_name}")
                spawned_lanes.append(lane_name)

            self._spawn_experimental_watcher()
        except Exception:
            for lane_name in spawned_lanes:
                try:
                    self.adapter.kill_lane(lane_name)
                except Exception:
                    pass
            raise

        if self.mode in {"baseline", "both"}:
            baseline_script = resolve_project_runtime_file(self.project_root, "pipeline-watcher-v3-logged.sh")
            baseline_log = self.base_dir / "logs" / "baseline" / "watcher.log"
            baseline_command = (
                f"exec bash {shlex.quote(str(baseline_script))} {shlex.quote(str(self.project_root))} "
                f"> {shlex.quote(str(baseline_log))} 2>&1"
            )
            baseline_info = self.adapter.spawn_watcher(window_name="watcher-baseline", shell_command=baseline_command)
            self.base_dir.joinpath("baseline.pid").write_text(str(baseline_info.get("pid") or ""), encoding="utf-8")

        self._start_token_collector()
        self._runtime_started = True
        self._write_current_run_pointer()
```

> 참고: `TmuxAdapter.kill_lane(lane_name)` 메서드가 없으면 `self.adapter.kill_session()` 대신 `kill_session` 후 재스캐폴드하는 방향으로 구현한다. TmuxAdapter 인터페이스를 먼저 확인할 것.

- [ ] **Step 4: TmuxAdapter에 kill_lane 필요 여부 확인**

```bash
grep -n "def kill" /home/xpdlqj/code/projectH/pipeline_runtime/tmux_adapter.py
```

`kill_lane`이 없으면 `kill_session`을 사용하도록 cleanup 코드를 조정한다:

```python
        except Exception:
            # 개별 lane kill 대신 session 전체 정리 (atomic cleanup)
            try:
                self.adapter.kill_session()
            except Exception:
                pass
            raise
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_spawn_runtime_session -v
```

---

### 2-C. P16: Codex 업데이트 메뉴 키 "3\r" 하드코딩

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_pipeline_runtime_cli.py` 내 기존 `test_codex_update_prompt_is_auto_dismissed_with_skip_until_next_version` 옆에 추가:

```python
def test_codex_update_auto_dismiss_uses_parsed_number_not_hardcoded(self) -> None:
    """메뉴에서 'skip until next version' 항목의 번호를 파싱해 사용해야 한다.
    항목이 3번이 아닌 경우에도 올바른 번호를 전송해야 한다."""
    sent: list[bytes] = []
    emitter = self._make_emitter(send_child_bytes=lambda b: sent.append(b))
    # skip until next version이 2번에 있는 메뉴
    menu_text = (
        "update available\n"
        "1) Install now\n"
        "2) skip until next version\n"
        "3) Cancel\n"
    )
    emitter.feed(menu_text)
    self.assertTrue(sent, "Should have sent a keypress")
    # 2번을 선택해야 한다 (하드코딩된 3이 아님)
    self.assertEqual(sent[-1], b"2\r")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_cli -k test_codex_update_auto_dismiss_uses_parsed -v
```

Expected: FAIL — `b"3\r"` 전송됨

- [ ] **Step 3: 수정 적용 — cli.py lines 1120–1133**

```python
    def _maybe_auto_dismiss_blocking_prompt(self, text: str) -> bool:
        if self.lane_name != "Codex":
            return False
        lower = text.lower()
        if not all(marker in lower for marker in _CODEX_UPDATE_SKIP_MARKERS):
            return False
        action_key = "codex_update_skip_until_next_version"
        if action_key in self._auto_actions_sent:
            return True
        # "skip until next version" 항목 번호를 동적으로 파싱한다.
        # 번호가 변경돼도 올바른 키를 전송할 수 있도록 하드코딩을 피한다.
        import re as _re
        match = _re.search(
            r"^\s*([1-9][0-9]?)\s*[\.\)]\s*skip until next version",
            text,
            _re.MULTILINE | _re.IGNORECASE,
        )
        key = f"{match.group(1)}\r".encode() if match else b"3\r"
        self.send_child_bytes(key)
        self._auto_actions_sent.add(action_key)
        return True
```

- [ ] **Step 4: 테스트 통과 확인 + 기존 테스트 회귀 없음**

```bash
python3 -m unittest tests.test_pipeline_runtime_cli -k codex_update -v
```

Expected: 전체 PASS

---

### 2-D. P18: _emit_task_done의 control_seq 타입 변환 방어 부재

- [ ] **Step 1: 수정 적용 — cli.py lines 962–964**

```python
# Before
        payload = {
            "job_id": str(self.accepted_payload.get("job_id") or ""),
            "control_seq": int(self.accepted_payload.get("control_seq") or -1),
            "dispatch_id": str(self.accepted_payload.get("dispatch_id") or ""),
        }

# After
        raw_seq = self.accepted_payload.get("control_seq")
        try:
            control_seq_val = int(raw_seq) if raw_seq is not None else -1
        except (TypeError, ValueError):
            control_seq_val = -1
        payload = {
            "job_id": str(self.accepted_payload.get("job_id") or ""),
            "control_seq": control_seq_val,
            "dispatch_id": str(self.accepted_payload.get("dispatch_id") or ""),
        }
```

- [ ] **Step 2: 컴파일 + 기존 테스트 통과 확인**

```bash
python3 -m py_compile pipeline_runtime/cli.py && \
python3 -m unittest tests.test_pipeline_runtime_cli -v 2>&1 | tail -5
```

---

### 2-E. P13: 레거시 current_run.json에서 fingerprint 없을 때 watcher 종료 건너뜀

- [ ] **Step 1: 수정 적용 — supervisor.py lines 2580–2590**

fingerprint가 없을 때 cwd 체크에 더해 cmdline 기반 추가 확인을 추가한다:

```python
# Before
        elif self._process_cwd(pid) != str(self.project_root.resolve()):
            return killed

# After
        elif self._process_cwd(pid) != str(self.project_root.resolve()):
            # cwd 불일치인 경우 cmdline도 확인해 watcher_core 프로세스가 맞는지 검증
            cmd = self._process_cmdline(pid)
            if "watcher_core.py" not in cmd and "pipeline-watcher-v3" not in cmd:
                return killed
            # cmdline에 watcher_core가 있지만 cwd가 다른 프로젝트 → 다른 프로젝트 watcher, 건너뜀
            return killed
```

> 이 수정은 현재 동작을 문서화하는 수준이므로 별도 테스트보다 컴파일 확인으로 충분하다.

- [ ] **Step 2: 컴파일 확인**

```bash
python3 -m py_compile pipeline_runtime/supervisor.py && echo "OK"
```

- [ ] **Step 3: Task 2 전체 검증 및 커밋**

```bash
python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/cli.py
python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_cli -v 2>&1 | tail -20
```

```bash
git add pipeline_runtime/supervisor.py pipeline_runtime/cli.py \
        tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_cli.py
git commit -m "fix(launcher): P8/P11/P13/P16/P18 logic correctness

- _spawn_runtime_session: clean up spawned lanes on failure (P8)
- _maybe_recover_lane: protect all owners post-accept, not only implement (P11)
- _terminate_current_run_watcher: document cwd+cmdline fallback behavior (P13)
- _maybe_auto_dismiss_blocking_prompt: parse menu number instead of hardcoding '3' (P16)
- _emit_task_done: guard control_seq type coercion (P18)"
```

---

## Task 3: 성능 — 캐싱 (P3, P4)

**Files:**
- Modify: `pipeline_runtime/supervisor.py` (`__init__`, `_control_handoff_sha`, `_duplicate_control_marker`)
- Test: `tests/test_pipeline_runtime_supervisor.py`

---

### 3-A. P4: _control_handoff_sha가 매 폴마다 파일 전체를 SHA256 계산

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_control_handoff_sha_uses_mtime_cache(self) -> None:
    """같은 mtime이면 파일을 다시 읽지 않고 캐시된 SHA를 반환해야 한다."""
    from unittest.mock import patch

    control_path = self.supervisor.base_dir / "implement_handoff.md"
    control_path.parent.mkdir(parents=True, exist_ok=True)
    control_path.write_text("content", encoding="utf-8")
    control = {"active_control_file": "implement_handoff.md", "active_control_status": "implement"}

    read_calls: list[str] = []
    original_read_bytes = pathlib.Path.read_bytes

    def tracking_read_bytes(self_path):
        read_calls.append(str(self_path))
        return original_read_bytes(self_path)

    import pathlib
    with patch.object(pathlib.Path, "read_bytes", tracking_read_bytes):
        sha1 = self.supervisor._control_handoff_sha(control)
        sha2 = self.supervisor._control_handoff_sha(control)

    self.assertEqual(sha1, sha2)
    # 두 번째 호출은 캐시를 써야 하므로 read_bytes가 한 번만 불려야 한다
    matching = [c for c in read_calls if "implement_handoff" in c]
    self.assertEqual(len(matching), 1, "read_bytes should be called only once for same mtime")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_control_handoff_sha_uses_mtime_cache -v
```

Expected: FAIL — `read_bytes` 2회 호출됨

- [ ] **Step 3: 수정 적용 — supervisor.py `__init__` 및 `_control_handoff_sha`**

`__init__` 내 기존 멤버 변수들 선언 블록 끝에 추가:

```python
        self._control_sha_cache: dict[str, tuple[float, str]] = {}  # path -> (mtime, sha256)
```

`_control_handoff_sha` 메서드를 교체:

```python
    def _control_handoff_sha(self, control: dict[str, Any]) -> str:
        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return ""
        try:
            mtime = control_path.stat().st_mtime
        except OSError:
            return ""
        cache_key = str(control_path)
        cached = self._control_sha_cache.get(cache_key)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        try:
            sha = hashlib.sha256(control_path.read_bytes()).hexdigest()
        except OSError:
            return ""
        self._control_sha_cache[cache_key] = (mtime, sha)
        return sha
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_control_handoff_sha -v
```

Expected: PASS

---

### 3-B. P3: _duplicate_control_marker가 raw.jsonl 400줄을 매 폴마다 재파싱

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_duplicate_control_marker_caches_result_for_same_key(self) -> None:
    """같은 (control_path, handoff_sha, updated_at) 조합이면 raw.jsonl을 다시 읽지 않아야 한다."""
    from unittest.mock import patch

    control_path = self.supervisor.base_dir / "implement_handoff.md"
    control_path.parent.mkdir(parents=True, exist_ok=True)
    control_path.write_text("STATUS: implement\nCONTROL_SEQ: 1\n", encoding="utf-8")

    control = {
        "active_control_file": "implement_handoff.md",
        "active_control_status": "implement",
        "active_control_seq": 1,
        "active_control_updated_at": "2026-05-21T00:00:00Z",
    }

    read_calls = []
    original_read_text = pathlib.Path.read_text

    def tracking_read_text(self_path, *args, **kwargs):
        if "raw.jsonl" in str(self_path):
            read_calls.append(str(self_path))
        return original_read_text(self_path, *args, **kwargs)

    import pathlib
    with patch.object(pathlib.Path, "read_text", tracking_read_text):
        self.supervisor._duplicate_control_marker(control)
        self.supervisor._duplicate_control_marker(control)

    self.assertLessEqual(
        len(read_calls), 1,
        "raw.jsonl should be read at most once for the same control key",
    )
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_duplicate_control_marker_caches -v
```

Expected: FAIL — raw.jsonl이 2회 이상 읽힘

- [ ] **Step 3: 수정 적용 — supervisor.py `__init__` 및 `_duplicate_control_marker`**

`__init__` 내 추가:

```python
        self._duplicate_marker_cache_key: str = ""
        self._duplicate_marker_cache_result: dict[str, Any] | None = None
```

`_duplicate_control_marker` 메서드 내 artifact_truth 검사 이후, raw.jsonl 읽기 직전에 캐시 체크 삽입:

```python
    def _duplicate_control_marker(self, control: dict[str, Any]) -> dict[str, Any] | None:
        snapshot = active_control_snapshot_from_status(control)
        if str(snapshot.get("control_status") or "") != "implement":
            return None
        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return None
        handoff_sha = self._control_handoff_sha(control)
        if not handoff_sha:
            return None
        control_seq = snapshot_control_seq(snapshot)
        active_control_updated_at = parse_iso_utc(str(snapshot.get("control_updated_at") or ""))
        completed_truth = completed_implement_handoff_truth(
            control_path,
            repo_root=self.project_root,
            work_root=self.project_root / "work",
            verify_root=self.project_root / "verify",
            active_control_updated_at=active_control_updated_at,
        )
        if completed_truth is not None:
            return {
                "control_file": str(snapshot.get("control_file") or ""),
                "control_seq": control_seq,
                "handoff_sha": handoff_sha,
                "reason": "handoff_already_completed",
                "blocked_fingerprint": str(completed_truth.get("work_path") or ""),
                "routed_to": VERIFY_TRIAGE_ESCALATION,
                "source_event": "artifact_truth_completed",
                "work_path": str(completed_truth.get("work_path") or ""),
                "verify_path": str(completed_truth.get("verify_path") or ""),
            }

        # raw.jsonl 읽기 캐시: 같은 (control_path, handoff_sha, updated_at) 조합이면 건너뜀
        cache_key = f"{control_path}|{handoff_sha}|{active_control_updated_at}"
        if cache_key == self._duplicate_marker_cache_key:
            return self._duplicate_marker_cache_result

        raw_log = self.base_dir / "logs" / "experimental" / "raw.jsonl"
        if not raw_log.exists():
            self._duplicate_marker_cache_key = cache_key
            self._duplicate_marker_cache_result = None
            return None
        try:
            raw_lines = raw_log.read_text(encoding="utf-8").splitlines()
        except OSError:
            self._duplicate_marker_cache_key = cache_key
            self._duplicate_marker_cache_result = None
            return None
        # ... (이하 기존 로직 유지) ...

        # 메서드 끝부분 return 직전에 캐시 갱신
        self._duplicate_marker_cache_key = cache_key
        self._duplicate_marker_cache_result = fallback
        return fallback
```

> 주의: 메서드의 기존 `return marker` 분기들에도 캐시 갱신을 추가해야 한다. 각 조기 반환 직전에 `self._duplicate_marker_cache_key = cache_key; self._duplicate_marker_cache_result = <result>` 패턴을 삽입한다.

- [ ] **Step 4: 테스트 통과 확인 + 기존 테스트 회귀 없음**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k duplicate -v
```

Expected: 전체 PASS

- [ ] **Step 5: Task 3 전체 검증 및 커밋**

```bash
python3 -m py_compile pipeline_runtime/supervisor.py
python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -10
```

```bash
git add pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py
git commit -m "perf(launcher): P3/P4 caching for SHA256 and raw.jsonl reads

- _control_handoff_sha: mtime-keyed cache prevents per-poll file reads (P4)
- _duplicate_control_marker: control-key cache prevents per-poll raw.jsonl re-parse (P3)"
```

---

## Task 4: 구조적 안정성 (P1, P2, P5, P7)

**Files:**
- Modify: `pipeline_runtime/supervisor.py` (`__init__`, `_prepare_runtime_surfaces`, `_build_artifacts`)
- Modify: `pipeline_runtime/cli.py` (`_spawn_supervisor`, `_inherited_run_id_from_live_watcher`)
- Test: `tests/test_pipeline_runtime_supervisor.py`
- Test: `tests/test_pipeline_runtime_cli.py`

---

### 4-A. P1: 재시작 시 raw.jsonl 초기화로 중복 핸드오프 탐지 실패

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_prepare_runtime_surfaces_preserves_raw_jsonl(self) -> None:
    """_prepare_runtime_surfaces 호출 후 raw.jsonl이 빈 파일로 초기화되면 안 된다."""
    raw_log = self.supervisor.base_dir / "logs" / "experimental" / "raw.jsonl"
    raw_log.parent.mkdir(parents=True, exist_ok=True)
    raw_log.write_text('{"event":"implement_blocked_detected"}\n', encoding="utf-8")

    self.supervisor._prepare_runtime_surfaces()

    content = raw_log.read_text(encoding="utf-8")
    self.assertIn("implement_blocked_detected", content,
                  "raw.jsonl must not be cleared on restart — needed for duplicate detection")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_prepare_runtime_surfaces_preserves_raw -v
```

Expected: FAIL — raw.jsonl 내용이 지워짐

- [ ] **Step 3: 수정 적용 — supervisor.py lines 2648–2654**

```python
# Before
        for log_name in [
            "watcher.log",
            "raw.jsonl",
            "dispatch.jsonl",
            "pipeline-launcher-start.log",
        ]:
            (self.base_dir / "logs" / "experimental" / log_name).write_text("", encoding="utf-8")

# After
        for log_name in [
            "watcher.log",
            # raw.jsonl은 초기화하지 않는다.
            # _duplicate_control_marker가 재시작 후에도 이전 implement_blocked 이벤트를
            # 읽어야 중복 핸드오프를 탐지할 수 있다.
            "dispatch.jsonl",
            "pipeline-launcher-start.log",
        ]:
            (self.base_dir / "logs" / "experimental" / log_name).write_text("", encoding="utf-8")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_prepare_runtime_surfaces -v
```

---

### 4-B. P2: events.jsonl에 dispatch_selection 이벤트가 매초 기록되어 무한 증가

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_build_artifacts_dispatch_selection_not_emitted_when_unchanged(self) -> None:
    """_build_artifacts를 반복 호출해도 latest_work/verify가 같으면 dispatch_selection 이벤트가 한 번만 기록되어야 한다."""
    # work/verify 디렉터리 없이 호출 → "—" 반환 케이스
    events_before = self._count_events("dispatch_selection")
    self.supervisor._build_artifacts()
    self.supervisor._build_artifacts()
    self.supervisor._build_artifacts()
    events_after = self._count_events("dispatch_selection")
    self.assertEqual(
        events_after - events_before, 1,
        "dispatch_selection should be emitted only when values change, not every poll",
    )
```

> `_count_events` 헬퍼가 없으면 아래처럼 추가:

```python
def _count_events(self, event_type: str) -> int:
    if not self.supervisor.events_path.exists():
        return 0
    count = 0
    for line in self.supervisor.events_path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            if entry.get("event_type") == event_type:
                count += 1
        except Exception:
            pass
    return count
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k test_build_artifacts_dispatch_selection_not_emitted_when_unchanged -v
```

Expected: FAIL — 3회 호출 시 이벤트 3회 기록

- [ ] **Step 3: 수정 적용 — supervisor.py `__init__` 및 `_build_artifacts`**

`__init__` 내 추가:

```python
        self._last_dispatch_selection_key: str = ""
```

`_build_artifacts` 내 `self._append_event("dispatch_selection", ...)` 호출 부분을 조건부로 변경:

```python
        dispatch_key = f"{work_rel}|{verify_rel}"
        if dispatch_key != self._last_dispatch_selection_key:
            self._last_dispatch_selection_key = dispatch_key
            self._append_event(
                "dispatch_selection",
                {
                    "latest_work": work_rel,
                    "latest_verify": verify_rel,
                    "date_key": work_date_key,
                    "latest_work_mtime": work_mtime,
                    "latest_verify_date_key": verify_date_key,
                    "latest_verify_mtime": verify_mtime,
                },
            )
```

- [ ] **Step 4: 기존 테스트 `test_build_artifacts_emits_dispatch_selection_event` 호환성 확인**

기존 테스트는 이벤트가 발생하는 케이스(값이 바뀐 상황)를 테스트하므로 그대로 통과해야 한다.

```bash
python3 -m unittest tests.test_pipeline_runtime_supervisor -k dispatch_selection -v
```

Expected: 전체 PASS

---

### 4-C. P5: 동시 start 시 중복 supervisor 생성 가능

- [ ] **Step 1: 수정 적용 — cli.py `_spawn_supervisor` 함수**

`import fcntl`을 파일 상단 import 블록에 추가한 뒤 `_spawn_supervisor` 내 첫 줄에 잠금을 추가:

```python
def _spawn_supervisor(args: argparse.Namespace) -> int:
    project_root, mode = _normalize_project_and_mode(args)
    session_name = args.session or _session_name_for(project_root)

    # 동시 start 실행을 직렬화하는 파일 잠금
    lock_path = project_root / ".pipeline" / ".supervisor-start.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_WRONLY)
    except OSError:
        lock_fd = -1

    try:
        if lock_fd >= 0:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                # 다른 start가 이미 실행 중 — 정상 종료
                return 0

        # ... 기존 _spawn_supervisor 로직 전체 ...
        reload_live_supervisor = _runtime_source_newer_than_supervisor_pidfile(project_root)
        # (이하 기존 코드 그대로)
    finally:
        if lock_fd >= 0:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            except OSError:
                pass
```

- [ ] **Step 2: 컴파일 확인**

```bash
python3 -m py_compile pipeline_runtime/cli.py && echo "OK"
```

---

### 4-D. P7: _inherited_run_id_from_live_watcher의 TOCTOU 경쟁

- [ ] **Step 1: 수정 적용 — supervisor.py `_inherited_run_id_from_live_watcher`**

fingerprint 비교 통과 후 pid를 재확인하는 코드를 추가:

```python
        if not pointer_fingerprint or pointer_fingerprint != live_fingerprint:
            return ""
        # TOCTOU 완화: fingerprint 검증 후 pid가 여전히 살아있는지 재확인
        if self._live_experimental_watcher_pid() != watcher_pid:
            return ""
        return candidate
```

- [ ] **Step 2: 컴파일 확인**

```bash
python3 -m py_compile pipeline_runtime/supervisor.py && echo "OK"
```

- [ ] **Step 3: Task 4 전체 검증 및 커밋**

```bash
python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/cli.py
python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_cli -v 2>&1 | tail -20
```

Expected: 전체 PASS

```bash
git add pipeline_runtime/supervisor.py pipeline_runtime/cli.py \
        tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_cli.py
git commit -m "fix(launcher): P1/P2/P5/P7 structural stability

- _prepare_runtime_surfaces: preserve raw.jsonl across restarts (P1)
- _build_artifacts: suppress repeated dispatch_selection events (P2)
- _spawn_supervisor: serialize concurrent start with flock (P5)
- _inherited_run_id_from_live_watcher: re-verify pid after fingerprint match (P7)"
```

---

## 최종 검증

- [ ] **전체 파이프라인 런타임 테스트 통과**

```bash
python3 -m unittest \
  tests.test_pipeline_runtime_supervisor \
  tests.test_pipeline_runtime_cli \
  tests.test_pipeline_runtime_automation_health \
  tests.test_pipeline_runtime_schema \
  -v 2>&1 | tail -30
```

Expected: 전체 PASS, 0 failures

- [ ] **컴파일 검사**

```bash
python3 -m py_compile \
  pipeline_runtime/supervisor.py \
  pipeline_runtime/cli.py \
  pipeline_runtime/automation_health.py \
  pipeline_runtime/schema.py
echo "컴파일 OK"
```

- [ ] **한국어 /work 클로즈아웃 작성**

`work/5/21/` 아래에 이번 라운드 변경 내역, 수정 파일, 검증 결과를 담은 클로즈아웃 노트를 작성하고 종료한다.

---

## 구현 우선순위 참고

급한 순서: **Task 1 → Task 4-A(P1) → Task 4-B(P2) → Task 2 → Task 3 → Task 4-C/D**

P1(raw.jsonl 초기화)과 P2(events.jsonl 무한 증가)는 장기 실행 안정성에 직접 영향을 주므로 Task 1 직후에 처리한다.
