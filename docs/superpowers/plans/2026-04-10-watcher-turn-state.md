# Watcher Turn State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a single `WatcherTurnState` enum and `turn_state.json` projection in watcher_core.py to unify turn ordering, eliminate stale control confusion, fix the Claude-before-Codex bug, add Claude idle timeout recovery, and let the GUI read one authoritative state file.

**Architecture:** A `WatcherTurnState` enum replaces scattered flags (`_waiting_for_claude`, `_pending_claude_handoff_sig`). All turn transitions go through `_transition_turn()`, which writes `.pipeline/state/turn_state.json` atomically. `backend.py` reads this file exclusively when present, falling back to legacy slot parsing only when absent.

**Tech Stack:** Python 3.11+, unittest, existing watcher_core.py / pipeline_gui infrastructure.

**Spec:** `docs/superpowers/specs/2026-04-10-watcher-turn-state-design.md`

---

## File Structure

| File | Role | Change Type |
|------|------|-------------|
| `watcher_core.py` | Core watcher — enum, transition, turn logic, idle timeout | Modify |
| `pipeline_gui/backend.py` | GUI backend — read turn_state.json, format display | Modify |
| `pipeline_gui/app.py` | GUI app — use updated backend output | Modify (minimal) |
| `tests/test_watcher_core.py` | Watcher unit tests | Modify |
| `tests/test_pipeline_gui_backend.py` | Backend unit tests | Modify |
| `.pipeline/README.md` | Pipeline policy docs | Modify |

---

### Task 1: WatcherTurnState Enum and `_transition_turn()` Method

**Files:**
- Modify: `watcher_core.py:96-113` (after JobStatus enum)
- Modify: `watcher_core.py:1408-1612` (WatcherCore.__init__)
- Test: `tests/test_watcher_core.py`

- [ ] **Step 1: Write failing test for WatcherTurnState enum**

```python
class TurnStateEnumTest(unittest.TestCase):
    def test_turn_state_values(self) -> None:
        from watcher_core import WatcherTurnState
        expected = {"IDLE", "CLAUDE_ACTIVE", "CODEX_VERIFY", "CODEX_FOLLOWUP",
                    "GEMINI_ADVISORY", "OPERATOR_WAIT"}
        self.assertEqual(set(e.value for e in WatcherTurnState), expected)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::TurnStateEnumTest::test_turn_state_values -v`
Expected: FAIL with `ImportError: cannot import name 'WatcherTurnState'`

- [ ] **Step 3: Add WatcherTurnState enum to watcher_core.py**

Add after the `TERMINAL_STATES` line (after line 113):

```python
class WatcherTurnState(str, Enum):
    IDLE             = "IDLE"
    CLAUDE_ACTIVE    = "CLAUDE_ACTIVE"
    CODEX_VERIFY     = "CODEX_VERIFY"
    CODEX_FOLLOWUP   = "CODEX_FOLLOWUP"
    GEMINI_ADVISORY  = "GEMINI_ADVISORY"
    OPERATOR_WAIT    = "OPERATOR_WAIT"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::TurnStateEnumTest::test_turn_state_values -v`
Expected: PASS

- [ ] **Step 5: Write failing test for `_transition_turn()` and turn_state.json**

```python
class TransitionTurnTest(unittest.TestCase):
    def test_transition_writes_turn_state_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CODEX_VERIFY,
                "work_needs_verify",
                active_control_file="claude_handoff.md",
                active_control_seq=17,
                verify_job_id="test-job-1",
            )

            state_path = base_dir / "state" / "turn_state.json"
            self.assertTrue(state_path.exists())
            data = json.loads(state_path.read_text())
            self.assertEqual(data["state"], "CODEX_VERIFY")
            self.assertEqual(data["reason"], "work_needs_verify")
            self.assertEqual(data["active_control_file"], "claude_handoff.md")
            self.assertEqual(data["active_control_seq"], 17)
            self.assertEqual(data["verify_job_id"], "test-job-1")
            self.assertIn("entered_at", data)

    def test_transition_updates_internal_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
                "startup",
            )
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)

            core._transition_turn(
                watcher_core.WatcherTurnState.IDLE,
                "claude_idle_timeout",
            )
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IDLE)
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::TransitionTurnTest -v`
Expected: FAIL with `AttributeError: 'WatcherCore' object has no attribute '_transition_turn'`

- [ ] **Step 7: Implement `_transition_turn()` in WatcherCore**

Add to `WatcherCore.__init__()` after the `_waiting_for_claude` line (around line 1612):

```python
        # Turn state (single source of truth for dispatch)
        self._current_turn_state: WatcherTurnState = WatcherTurnState.IDLE
        self._turn_entered_at: float = 0.0
        self._turn_state_path: Path = self.state_dir / "turn_state.json"
```

Add `_transition_turn()` method to WatcherCore (after `_session_arbitration_enabled`, around line 1722):

```python
    def _transition_turn(
        self,
        new_state: WatcherTurnState,
        reason: str,
        *,
        active_control_file: str = "",
        active_control_seq: int = -1,
        verify_job_id: str = "",
    ) -> None:
        """Transition to a new turn state and write turn_state.json atomically."""
        old_state = self._current_turn_state
        now = time.time()
        self._current_turn_state = new_state
        self._turn_entered_at = now
        log.info(
            "turn_state %s -> %s  reason=%s",
            old_state.value, new_state.value, reason,
        )
        self._log_raw(
            "turn_transition",
            "",
            "turn_state",
            {
                "from": old_state.value,
                "to": new_state.value,
                "reason": reason,
                "active_control_file": active_control_file,
                "active_control_seq": active_control_seq,
            },
        )
        # Write turn_state.json atomically
        data = {
            "state": new_state.value,
            "entered_at": now,
            "reason": reason,
            "active_control_file": active_control_file,
            "active_control_seq": active_control_seq,
        }
        if verify_job_id:
            data["verify_job_id"] = verify_job_id
        self.state_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self._turn_state_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp_path.replace(self._turn_state_path)
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::TransitionTurnTest -v`
Expected: PASS

- [ ] **Step 9: Run all existing tests to confirm no regressions**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py -v`
Expected: All existing tests PASS

- [ ] **Step 10: Commit**

```bash
git add watcher_core.py tests/test_watcher_core.py
git commit -m "feat: add WatcherTurnState enum and _transition_turn() method

Introduces single turn state axis for dispatch unification.
turn_state.json written atomically on every transition."
```

---

### Task 2: Replace `_determine_initial_turn()` with Transition-Based Turn Resolution

**Files:**
- Modify: `watcher_core.py:2144-2172` (`_determine_initial_turn`)
- Modify: `watcher_core.py:2727-2797` (`_poll` initial turn + waiting_for_claude)
- Test: `tests/test_watcher_core.py`

- [ ] **Step 1: Write failing test for new turn resolution — verify_pending blocks Claude**

```python
class TurnResolutionTest(unittest.TestCase):
    def test_codex_verify_before_claude_when_work_exists(self) -> None:
        """When work needs verify and handoff is active, Codex goes first."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            # Create active handoff
            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            # Create work note that needs verify (no same-day verify exists)
            work_note = watch_dir / "4" / "10" / "2026-04-10-some-work.md"
            _write_work_note(work_note, ["controller/server.py"])

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "codex")

    def test_claude_active_when_no_pending_verify(self) -> None:
        """When no work needs verify and handoff is active, Claude goes."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "claude")

    def test_idle_fallback_when_nothing_pending(self) -> None:
        """When no control signals and no work, state is IDLE."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "idle")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::TurnResolutionTest -v`
Expected: FAIL with `AttributeError: 'WatcherCore' object has no attribute '_resolve_turn'`

- [ ] **Step 3: Implement `_resolve_turn()` replacing `_determine_initial_turn()`**

Add new method to WatcherCore:

```python
    def _resolve_turn(self) -> str:
        """Resolve which agent should act next.

        Returns one of: "operator", "gemini", "codex_followup", "codex", "claude", "idle".
        This is a pure query — it does not trigger transitions or side effects.
        Used by both initial turn and rolling turn decisions.
        """
        # 1. operator_request active → operator
        if self._is_active_control(self.operator_request_path, "needs_operator"):
            return "operator"

        # 2. gemini_request active → gemini
        if self._is_active_control(self.gemini_request_path, "request_open"):
            return "gemini"

        # 3. gemini_advice active → codex_followup
        if self._is_active_control(self.gemini_advice_path, "advice_ready"):
            return "codex_followup"

        # 4. handoff active + implement, but verify_pending or verify_active → codex first
        handoff_active = self._is_active_control(self.claude_handoff_path, "implement")
        verify_pending = self._latest_work_needs_verify_broad()
        verify_active = self._claude_handoff_verify_active()
        if handoff_active and (verify_pending or verify_active):
            return "codex"

        # 5. work needs verify (no handoff) → codex
        if verify_pending:
            return "codex"

        # 6. handoff active and dispatchable → claude
        if handoff_active:
            return "claude"

        # 7. fallback
        return "idle"
```

Add `_latest_work_needs_verify_broad()` that does not filter metadata-only:

```python
    def _latest_work_needs_verify_broad(self) -> bool:
        """Like _latest_work_needs_verify but includes metadata-only notes.

        For verify-needed judgment, all canonical round notes count.
        Metadata-only filtering is only for dispatch prompt content.
        """
        latest_work = self._find_latest_md_broad(self.watch_dir)
        if latest_work is None:
            return False
        latest_verify = self._get_latest_same_day_verify_path(latest_work)
        work_mtime = self._get_path_mtime(latest_work)
        verify_mtime = self._get_path_mtime(latest_verify) if latest_verify else 0.0
        return work_mtime > verify_mtime

    def _find_latest_md_broad(self, root: Path) -> Optional[Path]:
        """Find latest canonical round note without metadata-only filtering."""
        latest_path: Optional[Path] = None
        latest_mtime = 0.0
        if not root.exists():
            return None
        for md in root.rglob("*.md"):
            if not self._is_canonical_round_note(root, md):
                continue
            try:
                mt = md.stat().st_mtime
            except OSError:
                continue
            if mt >= latest_mtime:
                latest_path = md
                latest_mtime = mt
        return latest_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::TurnResolutionTest -v`
Expected: PASS

- [ ] **Step 5: Write failing test for verify_pending blocks Claude even with metadata-only note**

```python
    def test_codex_verify_before_claude_even_for_metadata_only_note(self) -> None:
        """Metadata-only work note still triggers Codex verify before Claude."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            # Metadata-only note (only work/ path in changed files)
            meta_note = watch_dir / "4" / "10" / "2026-04-10-meta-only.md"
            _write_work_note(meta_note, ["work/4/10/2026-04-10-meta-only.md"])

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "codex")
```

- [ ] **Step 6: Run test to verify it passes** (should already pass from step 3)

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::TurnResolutionTest::test_codex_verify_before_claude_even_for_metadata_only_note -v`
Expected: PASS

- [ ] **Step 7: Wire `_resolve_turn()` into `_poll()` replacing `_determine_initial_turn()`**

Modify `_poll()` (around line 2738-2797). Replace the initial turn block:

```python
        # --- 시작 시 1회: 턴 판단 ---
        if not self._initial_turn_checked:
            self._initial_turn_checked = True
            turn = self._resolve_turn()
            log.info("initial turn: %s", turn)
            self._log_raw("initial_turn", "", "startup", {"turn": turn})
            if turn == "claude":
                self._work_baseline_snapshot = self._get_work_tree_snapshot()
                self._transition_turn(
                    WatcherTurnState.CLAUDE_ACTIVE,
                    "startup_turn_claude",
                    active_control_file="claude_handoff.md",
                    active_control_seq=self._read_control_seq_from_path(self.claude_handoff_path),
                )
                handoff_path, _ = self._get_latest_implement_handoff()
                self._notify_claude("startup_turn_claude", handoff_path)
                log.info("waiting_for_claude: baseline_files=%d",
                         len(self._work_baseline_snapshot))
                return
            if turn == "operator":
                self._transition_turn(WatcherTurnState.OPERATOR_WAIT, "startup_turn_operator")
                log.info("startup turn blocked by pending operator_request")
                self._log_raw(
                    "operator_request_pending",
                    str(self.operator_request_path),
                    "startup",
                    {"status": "needs_operator"},
                )
                return
            if turn == "gemini":
                self._transition_turn(WatcherTurnState.GEMINI_ADVISORY, "startup_turn_gemini")
                self._notify_gemini("startup_turn_gemini")
                return
            if turn == "codex_followup":
                self._transition_turn(WatcherTurnState.CODEX_FOLLOWUP, "startup_turn_codex_followup")
                self._notify_codex_followup("startup_turn_codex_followup")
                return
            if turn == "codex":
                self._transition_turn(WatcherTurnState.CODEX_VERIFY, "startup_turn_codex")
                # Codex verify는 work/ 감시 루프에서 자연스럽게 디스패치됨
                return
            # idle
            self._transition_turn(WatcherTurnState.IDLE, "startup_turn_idle")
```

Replace `_waiting_for_claude` check with `_current_turn_state`:

```python
        # --- Claude 차례 대기 중이면 work/ 감시 건너뜀 ---
        if self._current_turn_state == WatcherTurnState.CLAUDE_ACTIVE:
            if self._check_claude_implement_blocked():
                return
            self._check_claude_live_session_escalation()
            current_snapshot = self._get_work_tree_snapshot()
            if current_snapshot == self._work_baseline_snapshot:
                return
            self._transition_turn(WatcherTurnState.IDLE, "claude_activity_detected")
            self._work_baseline_snapshot = {}
            self._clear_session_arbitration_draft("claude_activity_resumed")
            self._clear_claude_blocked_state("claude_activity_resumed")
            log.info("claude activity detected by snapshot diff, resuming codex dispatch")
```

- [ ] **Step 8: Remove `_waiting_for_claude` flag**

In `__init__`, remove:
```python
        self._waiting_for_claude: bool = False
```

Replace all remaining references to `self._waiting_for_claude` with `self._current_turn_state == WatcherTurnState.CLAUDE_ACTIVE`. Search for `_waiting_for_claude` and update each occurrence.

- [ ] **Step 9: Run all watcher tests**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py -v`
Expected: All tests PASS (existing tests that reference `_waiting_for_claude` will need adjustment — update them to check `_current_turn_state == WatcherTurnState.CLAUDE_ACTIVE` instead)

- [ ] **Step 10: Commit**

```bash
git add watcher_core.py tests/test_watcher_core.py
git commit -m "feat: replace _determine_initial_turn with _resolve_turn and transition path

Initial turn now uses same _resolve_turn() as rolling updates.
verify_pending/verify_active blocks Claude even when handoff is active.
Metadata-only notes included in verify-needed judgment.
_waiting_for_claude replaced by WatcherTurnState.CLAUDE_ACTIVE."
```

---

### Task 3: Wire `_transition_turn()` into Rolling Signal Updates

**Files:**
- Modify: `watcher_core.py:2319-2426` (`_check_pipeline_signal_updates`)
- Modify: `watcher_core.py:2294-2316` (`_flush_pending_claude_handoff`)
- Test: `tests/test_watcher_core.py`

- [ ] **Step 1: Write failing test for stale control seq rejection**

```python
class RollingSignalTransitionTest(unittest.TestCase):
    def test_stale_control_seq_does_not_trigger_transition(self) -> None:
        """A signal with lower control_seq than current should not cause transition."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            # Set current state with seq 17
            core._transition_turn(
                watcher_core.WatcherTurnState.CODEX_VERIFY,
                "test_setup",
                active_control_seq=17,
            )

            # A handoff with lower seq should not override
            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 15\n", encoding="utf-8")
            core._check_pipeline_signal_updates()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CODEX_VERIFY)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::RollingSignalTransitionTest -v`
Expected: FAIL (current code doesn't check against turn state seq)

- [ ] **Step 3: Add seq guard to `_check_pipeline_signal_updates()`**

In `_check_pipeline_signal_updates()`, before each notify call, add a guard that checks:
1. The signal's control_seq must be >= the current turn state's `active_control_seq` (stored in `_turn_active_control_seq` internal field)
2. If equal seq, the canonical resolver (`_get_active_control_signal()`) must have selected this signal as winner

Add to `__init__`:
```python
        self._turn_active_control_seq: int = -1
```

Update `_transition_turn()` to track this:
```python
        self._turn_active_control_seq = active_control_seq
```

In `_check_pipeline_signal_updates()`, add at the claude handoff section (around line 2393-2424):

```python
            if (
                active_control is not None
                and active_control.path == self.claude_handoff_path
                and status == "implement"
                and dispatch_state["dispatchable"]
                and active_control.control_seq >= self._turn_active_control_seq
            ):
```

Apply similar guard to gemini_request, gemini_advice, and operator_request sections.

- [ ] **Step 4: Add transitions to `_check_pipeline_signal_updates()`**

After each successful notify, add the corresponding `_transition_turn()` call:

For claude handoff notify (line ~2401):
```python
                self._transition_turn(
                    WatcherTurnState.CLAUDE_ACTIVE,
                    "claude_handoff_updated",
                    active_control_file="claude_handoff.md",
                    active_control_seq=active_control.control_seq,
                )
                self._work_baseline_snapshot = self._get_work_tree_snapshot()
```

For gemini request notify (line ~2355):
```python
                self._transition_turn(
                    WatcherTurnState.GEMINI_ADVISORY,
                    "gemini_request_updated",
                    active_control_file="gemini_request.md",
                    active_control_seq=active_control.control_seq if active_control else -1,
                )
```

For gemini advice notify (line ~2375):
```python
                self._transition_turn(
                    WatcherTurnState.CODEX_FOLLOWUP,
                    "gemini_advice_updated",
                    active_control_file="gemini_advice.md",
                    active_control_seq=active_control.control_seq if active_control else -1,
                )
```

For operator request (line ~2328):
```python
                self._transition_turn(
                    WatcherTurnState.OPERATOR_WAIT,
                    "operator_request_updated",
                    active_control_file="operator_request.md",
                    active_control_seq=active_control.control_seq,
                )
```

- [ ] **Step 5: Remove `_pending_claude_handoff_sig` flag**

Replace `_pending_claude_handoff_sig` usage in `_flush_pending_claude_handoff()`. Instead, when verify lease releases and current turn is `CODEX_VERIFY`, re-resolve turn:

```python
    def _flush_pending_claude_handoff(self) -> None:
        """If verify lease just released and handoff is waiting, transition to Claude."""
        if self._current_turn_state != WatcherTurnState.CODEX_VERIFY:
            return
        if self._claude_handoff_verify_active():
            return  # verify still running

        # Re-resolve: maybe Claude can go now
        turn = self._resolve_turn()
        if turn == "claude":
            handoff_path, _ = self._get_latest_implement_handoff()
            active_control = self._get_active_control_signal()
            self._transition_turn(
                WatcherTurnState.CLAUDE_ACTIVE,
                "verify_lease_released",
                active_control_file="claude_handoff.md",
                active_control_seq=active_control.control_seq if active_control else -1,
            )
            self._work_baseline_snapshot = self._get_work_tree_snapshot()
            self._notify_claude("verify_lease_released", handoff_path)
```

Remove `_pending_claude_handoff_sig` from `__init__`.

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::RollingSignalTransitionTest -v`
Expected: PASS

- [ ] **Step 7: Run all watcher tests**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add watcher_core.py tests/test_watcher_core.py
git commit -m "feat: wire _transition_turn into rolling signal updates

Stale control_seq signals no longer trigger transitions.
_pending_claude_handoff_sig replaced by turn state re-resolution.
All rolling notify paths now go through _transition_turn()."
```

---

### Task 4: Claude Idle Timeout with Progress Tracking

**Files:**
- Modify: `watcher_core.py` (WatcherCore.__init__ + _poll)
- Test: `tests/test_watcher_core.py`

- [ ] **Step 1: Write failing test for idle timeout**

```python
class ClaudeIdleTimeoutTest(unittest.TestCase):
    def test_claude_idle_timeout_transitions_to_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            # Simulate Claude active
            core._transition_turn(
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
                "test_setup",
            )
            core._last_progress_at = time.time() - 10  # 10 seconds ago
            core._work_baseline_snapshot = {}

            # Mock pane capture to return idle pane
            with mock.patch("watcher_core._capture_pane_text", return_value="$ "):
                with mock.patch("watcher_core._pane_text_is_idle", return_value=True):
                    core._check_claude_idle_timeout()

            self.assertEqual(
                core._current_turn_state,
                watcher_core.WatcherTurnState.IDLE,
            )

    def test_claude_progress_resets_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
                "test_setup",
            )
            core._last_progress_at = time.time() - 10

            # Simulate pane fingerprint changed
            core._last_active_pane_fingerprint = "old_fingerprint"
            with mock.patch("watcher_core._capture_pane_text", return_value="running tests..."):
                with mock.patch("watcher_core._pane_text_is_idle", return_value=False):
                    core._check_claude_idle_timeout()

            self.assertEqual(
                core._current_turn_state,
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
            )
            self.assertGreater(core._last_progress_at, time.time() - 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::ClaudeIdleTimeoutTest -v`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Implement idle timeout tracking**

Add to `__init__`:

```python
        self.claude_active_idle_timeout_sec: float = float(
            config.get("claude_active_idle_timeout_sec", 300)
        )
        self._last_progress_at: float = 0.0
        self._last_active_pane_fingerprint: str = ""
        self._last_idle_release_handoff_sig: str = ""
        self._last_idle_release_at: float = 0.0
```

Update `_transition_turn()` to reset progress tracking on CLAUDE_ACTIVE:

```python
        if new_state == WatcherTurnState.CLAUDE_ACTIVE:
            self._last_progress_at = now
            self._last_active_pane_fingerprint = ""
```

Add `_check_claude_idle_timeout()`:

```python
    def _check_claude_idle_timeout(self) -> None:
        """Check if Claude has been idle too long and transition to IDLE if so."""
        if self._current_turn_state != WatcherTurnState.CLAUDE_ACTIVE:
            return

        target = self._role_pane_target("implement")
        if not target:
            return

        now = time.time()
        pane_text = _capture_pane_text(target)
        pane_fingerprint = hashlib.md5(pane_text.encode()).hexdigest() if pane_text else ""

        # Check for progress: pane fingerprint changed
        if pane_fingerprint and pane_fingerprint != self._last_active_pane_fingerprint:
            self._last_active_pane_fingerprint = pane_fingerprint
            self._last_progress_at = now
            return

        # Check for progress: work snapshot changed
        current_snapshot = self._get_work_tree_snapshot()
        if current_snapshot != self._work_baseline_snapshot:
            self._last_progress_at = now
            return

        # No progress — check timeout
        elapsed = now - self._last_progress_at
        if elapsed < self.claude_active_idle_timeout_sec:
            return

        # Final guard: pane must look idle too
        if not _pane_text_is_idle(pane_text):
            return

        log.warning(
            "claude idle timeout: %.0fs since last progress, transitioning to IDLE",
            elapsed,
        )
        # Record cooldown to prevent immediate re-dispatch of same handoff
        self._last_idle_release_handoff_sig = self._get_path_sig(self.claude_handoff_path)
        self._last_idle_release_at = now
        self._transition_turn(WatcherTurnState.IDLE, "claude_idle_timeout")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py::ClaudeIdleTimeoutTest -v`
Expected: PASS

- [ ] **Step 5: Write failing test for re-dispatch cooldown**

```python
    def test_idle_release_cooldown_prevents_redispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            handoff_sig = core._get_path_sig(handoff)
            core._last_idle_release_handoff_sig = handoff_sig
            core._last_idle_release_at = time.time()

            # Resolve turn should NOT return claude due to cooldown
            self.assertTrue(core._is_idle_release_cooldown_active())
```

- [ ] **Step 6: Implement cooldown check**

```python
    def _is_idle_release_cooldown_active(self) -> bool:
        """True if the same handoff was recently released from idle timeout."""
        if not self._last_idle_release_handoff_sig:
            return False
        current_sig = self._get_path_sig(self.claude_handoff_path)
        if current_sig != self._last_idle_release_handoff_sig:
            return False
        elapsed = time.time() - self._last_idle_release_at
        return elapsed < self.claude_active_idle_timeout_sec
```

Update `_resolve_turn()` step 6 (claude branch):

```python
        # 6. handoff active and dispatchable → claude (unless cooldown)
        if handoff_active and not self._is_idle_release_cooldown_active():
            return "claude"
```

- [ ] **Step 7: Run all tests**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py -v`
Expected: All PASS

- [ ] **Step 8: Wire `_check_claude_idle_timeout()` into `_poll()`**

In the CLAUDE_ACTIVE block of `_poll()`, after the blocked/escalation checks and before the snapshot diff check:

```python
        if self._current_turn_state == WatcherTurnState.CLAUDE_ACTIVE:
            if self._check_claude_implement_blocked():
                return
            self._check_claude_live_session_escalation()
            self._check_claude_idle_timeout()
            if self._current_turn_state != WatcherTurnState.CLAUDE_ACTIVE:
                return  # idle timeout fired
            # ... existing snapshot diff check
```

- [ ] **Step 9: Run all tests**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py -v`
Expected: All PASS

- [ ] **Step 10: Commit**

```bash
git add watcher_core.py tests/test_watcher_core.py
git commit -m "feat: add Claude idle timeout with progress tracking and cooldown

CLAUDE_ACTIVE transitions to IDLE after N seconds without pane/work progress.
Same handoff sig is blocked from re-dispatch during cooldown period.
last_progress_at tracks pane fingerprint, work snapshot, and tree changes."
```

---

### Task 5: Backend `read_turn_state()` and Display Integration

**Files:**
- Modify: `pipeline_gui/backend.py:439-560` (`parse_control_slots`, `format_control_summary`)
- Modify: `pipeline_gui/app.py` (minimal — use updated backend)
- Test: `tests/test_pipeline_gui_backend.py`

- [ ] **Step 1: Write failing test for `read_turn_state()`**

```python
class TurnStateReadTest(unittest.TestCase):
    def test_read_turn_state_returns_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            turn_state = state_dir / "turn_state.json"
            turn_state.write_text(json.dumps({
                "state": "CODEX_VERIFY",
                "entered_at": 1744300000.0,
                "reason": "work_needs_verify",
                "active_control_file": "claude_handoff.md",
                "active_control_seq": 17,
            }))

            from pipeline_gui.backend import read_turn_state
            result = read_turn_state(root)
            self.assertIsNotNone(result)
            self.assertEqual(result["state"], "CODEX_VERIFY")

    def test_read_turn_state_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from pipeline_gui.backend import read_turn_state
            result = read_turn_state(root)
            self.assertIsNone(result)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_pipeline_gui_backend.py::TurnStateReadTest -v`
Expected: FAIL with `ImportError: cannot import name 'read_turn_state'`

- [ ] **Step 3: Implement `read_turn_state()` in backend.py**

Add after `current_verify_activity()` (around line 531):

```python
def read_turn_state(project: Path) -> dict[str, object] | None:
    """Read .pipeline/state/turn_state.json if present."""
    path = project / ".pipeline" / "state" / "turn_state.json"
    return _read_json_file(path)


_TURN_STATE_LABELS: dict[str, str] = {
    "IDLE": "대기",
    "CLAUDE_ACTIVE": "Claude 실행 중",
    "CODEX_VERIFY": "Codex 검증 중",
    "CODEX_FOLLOWUP": "Codex 후속 판단 중",
    "GEMINI_ADVISORY": "Gemini 자문 중",
    "OPERATOR_WAIT": "운영자 결정 대기",
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_pipeline_gui_backend.py::TurnStateReadTest -v`
Expected: PASS

- [ ] **Step 5: Write failing test for `format_control_summary` with turn_state**

```python
    def test_format_control_summary_uses_turn_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "turn_state.json").write_text(json.dumps({
                "state": "CODEX_VERIFY",
                "entered_at": 1744300000.0,
                "reason": "work_needs_verify",
                "active_control_file": "claude_handoff.md",
                "active_control_seq": 17,
            }))

            from pipeline_gui.backend import format_control_summary, parse_control_slots, read_turn_state
            parsed = parse_control_slots(root)
            turn = read_turn_state(root)
            active_text, _ = format_control_summary(parsed, turn_state=turn)
            self.assertIn("Codex 검증 중", active_text)
```

- [ ] **Step 6: Update `format_control_summary()` to accept and prefer turn_state**

Modify `format_control_summary()` signature and body:

```python
def format_control_summary(
    parsed: dict[str, object],
    *,
    verify_activity: dict[str, object] | None = None,
    turn_state: dict[str, object] | None = None,
) -> tuple[str, str]:
    """Return (active_text, stale_text) for display in the system card.

    If turn_state is provided, use it exclusively for active display.
    Do not mix turn_state with legacy slot parsing.
    """
    if turn_state is not None:
        state_value = str(turn_state.get("state") or "IDLE")
        label = _TURN_STATE_LABELS.get(state_value, state_value)
        control_file = str(turn_state.get("active_control_file") or "")
        seq = turn_state.get("active_control_seq")
        prov = f"seq {seq}" if seq is not None and seq >= 0 else ""
        parts = [f"활성 제어: {label}"]
        if control_file:
            parts.append(f"({control_file}")
            if prov:
                parts[-1] += f", {prov}"
            parts[-1] += ")"
        active_text = " ".join(parts)

        stale = parsed.get("stale") or []
        stale_text = ", ".join(
            f"{s['label']} ({s['file']})" for s in stale  # type: ignore[index]
        ) if stale else ""
        return active_text, stale_text

    # Legacy fallback — existing logic unchanged
    active = parsed.get("active")
    if verify_activity is not None:
        # ... existing verify_activity logic ...
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_pipeline_gui_backend.py::TurnStateReadTest -v`
Expected: PASS

- [ ] **Step 8: Update app.py to pass turn_state to format_control_summary**

In `app.py`, find where `format_control_summary()` is called and add `turn_state` parameter:

```python
        turn_state = read_turn_state(self.project_root)
        active_text, stale_text = format_control_summary(
            parsed,
            verify_activity=verify_activity,
            turn_state=turn_state,
        )
```

Add `read_turn_state` to the import from `backend`.

- [ ] **Step 9: Run all backend and app tests**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_pipeline_gui_backend.py tests/test_pipeline_gui_app.py -v`
Expected: All PASS

- [ ] **Step 10: Commit**

```bash
git add pipeline_gui/backend.py pipeline_gui/app.py tests/test_pipeline_gui_backend.py
git commit -m "feat: backend reads turn_state.json for unified control display

read_turn_state() reads .pipeline/state/turn_state.json.
format_control_summary() uses turn_state exclusively when present.
No mixing of turn_state with legacy slot parsing."
```

---

### Task 6: Documentation and Final Verification

**Files:**
- Modify: `.pipeline/README.md`
- Test: all test files

- [ ] **Step 1: Update .pipeline/README.md**

Add a section about `turn_state.json` after the existing control slot documentation:

```markdown
## turn_state.json

`.pipeline/state/turn_state.json`은 watcher가 매 턴 전이마다 atomic write하는 단일 상태 파일이다.

### 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `state` | string | `IDLE`, `CLAUDE_ACTIVE`, `CODEX_VERIFY`, `CODEX_FOLLOWUP`, `GEMINI_ADVISORY`, `OPERATOR_WAIT` |
| `entered_at` | float | 전이 시각 (epoch) |
| `reason` | string | 전이 사유 |
| `active_control_file` | string | 현재 active control slot 파일명 |
| `active_control_seq` | int | 현재 active CONTROL_SEQ (-1이면 없음) |
| `verify_job_id` | string | (선택) 현재 verify 대상 job ID |

### 규칙

- 이 파일은 watcher 내부 canonical state의 **UI 투영**이다. job state를 대체하지 않는다.
- `pipeline_gui/backend.py`는 이 파일이 있으면 **이것만** 읽어 표시한다. control slot 재해석과 혼합하지 않는다.
- 이 파일이 없으면 기존 control slot + job state 해석으로 fallback한다.
```

- [ ] **Step 2: Run full test suite**

Run: `cd /home/xpdlqj/code/projectH && python -m pytest tests/test_watcher_core.py tests/test_pipeline_gui_backend.py tests/test_pipeline_gui_app.py -v`
Expected: All PASS

- [ ] **Step 3: Verify turn_state.json is created in dry_run mode**

Run: `cd /home/xpdlqj/code/projectH && python -c "
import tempfile, json
from pathlib import Path
from tests.test_watcher_core import _write_active_profile
import watcher_core

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'work').mkdir(); (root / '.pipeline').mkdir()
    _write_active_profile(root)
    (root / '.pipeline' / 'claude_handoff.md').write_text('STATUS: implement\nCONTROL_SEQ: 1\n')
    core = watcher_core.WatcherCore({'watch_dir': str(root/'work'), 'base_dir': str(root/'.pipeline'), 'repo_root': str(root), 'dry_run': True, 'startup_grace_sec': 0})
    core._initial_turn_checked = False
    core._poll()
    ts = root / '.pipeline' / 'state' / 'turn_state.json'
    print('exists:', ts.exists())
    if ts.exists():
        print(json.loads(ts.read_text()))
"`
Expected: `exists: True` and JSON with `state: CLAUDE_ACTIVE`

- [ ] **Step 4: Commit**

```bash
git add .pipeline/README.md
git commit -m "docs: document turn_state.json in pipeline README"
```

- [ ] **Step 5: Final commit with all changes verified**

Run: `cd /home/xpdlqj/code/projectH && git log --oneline -6`

Verify 6 commits from this plan are present, all tests pass.

---

## Execution Summary

| Task | Focus | Key Output |
|------|-------|------------|
| 1 | Enum + `_transition_turn()` | `WatcherTurnState`, atomic JSON write |
| 2 | `_resolve_turn()` replacing initial turn | verify_pending blocks Claude, metadata-only fix |
| 3 | Rolling signal transitions | Stale seq rejection, remove `_pending_claude_handoff_sig` |
| 4 | Claude idle timeout | `last_progress_at`, cooldown, IDLE recovery |
| 5 | Backend integration | `read_turn_state()`, exclusive display path |
| 6 | Docs + final verification | README, full test suite |

## Not Implemented (per spec)

- `CLAUDE_STALLED` enum (2차)
- Bidirectional ack (설계 문서만, 구현 없음)
- Partial write settle for control slots
- Event-based architecture
- Pane crash auto-recovery
