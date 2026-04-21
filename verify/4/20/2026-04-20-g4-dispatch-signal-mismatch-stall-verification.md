# 2026-04-20 g4 dispatch signal mismatch stall verification

## 변경 파일
- `verify/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-verification.md`

## 사용 skill
- `round-handoff`: seq 584 implement handoff에 따른 최신 `/work`(AXIS-G4 stall-trace) 주장을 HEAD/파일/테스트/evidence run에 narrowest로 재대조했습니다.

## 변경 이유
- `work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall.md` 가 `.pipeline/claude_handoff.md` seq 584의 trace + test-skeleton 슬라이스를 닫았다고 주장했습니다. SCOPE_HINT는 code/test-skeleton + 신규 `/work` 파일이라서 verify 라인은 (a) 새 `/work` 파일 1개 + `tests/test_watcher_core.py`의 단일 테스트 메서드 append라는 파일 경계, (b) `tests.test_watcher_core` 재실행과 `git diff --check` 결과의 실제 값, (c) AXIS-G4 evidence 주장(run `20260420T142213Z-p817639`, seq 233–423, supervisor `lane_working`/wrapper `HEARTBEAT` only, empty `receipts/`)의 사실 일치, (d) `/work` 자체의 `## 검증` 섹션 진위성을 narrowest로 확인했습니다.

## 핵심 변경 (verify 관점 스냅샷)
- `work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall.md` 는 `## 변경 파일`, `## 사용 skill`, `## 변경 이유`, `## 핵심 변경`, `## 검증`, `## 남은 리스크` 섹션을 순서대로 보유. 단, `## 검증` 섹션 본문은 `실행 후 실제 결과를 아래에 기록합니다.` 한 줄만 있고 **실제 재실행 결과 수치가 비어 있음**. `/work README` 의 "실행하지 않은 명령이나 검증 결과를 추측으로 적지 않습니다" 규칙은 어기지 않았지만, implement 라인이 실제 명령을 돌리지 않았거나 수치를 옮기지 않은 상태로 닫혔다는 뜻. verify 라인이 아래 `## 검증` 섹션에 실제 수치를 직접 기록함.
- `tests/test_watcher_core.py` Grep 결과: `class WatcherDispatchQueueControlMismatchTest(unittest.TestCase):` 끝부분 line 2296–2299 에 `@unittest.skip("AXIS-G4 trace-only: fix slice not yet pinned")` + `def test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt(...)` 단일 메서드만 append 되어 있음. 동일 이름은 파일 전체에서 line 2297 단일 히트. `WatcherDispatchQueueControlMismatchTest` 클래스는 line 2143 부터 존재하며, append 이전 기존 메서드들은 byte-for-byte 유지.
- 파일 편집 범위: `git diff --check -- work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall.md tests/test_watcher_core.py` 출력 없음. production 모듈(`watcher_core.py`, `watcher_dispatch.py`, `pipeline_runtime/*`, 등) 은 이번 라운드에서 추가 편집되지 않음. 다른 test 모듈, `docs/projectH_pipeline_runtime_docs/*`, `.pipeline/*` control 슬롯(단 `.pipeline/claude_handoff.md` seq 584 본체는 이 라운드 입력 그대로 유지)도 이번 라운드 미변경.
- AXIS-G4 evidence 주장 재현:
  - `.pipeline/runs/20260420T142213Z-p817639/events.jsonl` 는 722 라인. seq 236 `supervisor / lane_working` (ts `2026-04-20T14:27:43.555105Z`), seq 245 `supervisor / lane_working` (ts `2026-04-20T14:27:52.665550Z`), seq 423 `supervisor / lane_ready` (ts `2026-04-20T14:31:55.694763Z`) 모두 `/work` 가 인용한 그대로.
  - `.pipeline/runs/20260420T142213Z-p817639/receipts/` 는 비어 있음(ls 결과 엔트리 없음). `/work` 의 "receipts/ 디렉터리는 존재하지만 빈 상태" 와 일치.
  - `.pipeline/runs/20260420T142213Z-p817639/wrapper-events/claude.jsonl` 전체 카운트: `HEARTBEAT` 196, `READY` 1, `DISPATCH_SEEN` / `TASK_ACCEPTED` 0 건. seq 233–423 와 대응되는 시간 창(`14:27:43.555105Z`–`14:31:55.694763Z`) 으로 좁히면 `HEARTBEAT` 50 건 그대로, 다른 event_type 0건. `/work` 의 "HEARTBEAT 50건만 있고 `DISPATCH_SEEN` / `TASK_ACCEPTED` 는 0건" 주장 byte-exact.
- seq 584 `.pipeline/claude_handoff.md` 의 SCOPE_LIMITS 준수 상태:
  - `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` line 74 AXIS-G5 seq 581 pin 문장 byte-exact 유지.
  - `docs/projectH_pipeline_runtime_docs/verify_queue/2026-04-20-dispatcher-trace-backfill.md` untracked 엔트리 그대로 유지.
  - 다른 `.pipeline/*` 파일(`gemini_request.md` 582, `gemini_advice.md` 583, `operator_request.md` 579) 본체 미변경, SUPERSEDES chain 558 → 573 → 579 보존.

## 검증
- `python3 -m unittest tests.test_watcher_core` → `Ran 146 tests in 7.545s` / `FAILED (failures=1, skipped=1)`. 즉 146 total = 144 pass + 1 skip + 1 fail. **handoff 가 기대한 "144 green" baseline과 다름**.
  - skip 1 건은 이번 라운드 append 한 `test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt` (의도된 skip).
  - fail 1 건은 `tests.test_watcher_core.BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` at `tests/test_watcher_core.py:4654` (`self.assertFalse(ok)` / `AssertionError: True is not false`). 위치는 이번 라운드 append 한 line 2296–2299 영역 바깥. HEAD 기준 baseline은 139 green (stash 로 tracked 변경 제거 후 재실행 결과, `Ran 139 tests in 9.150s` / `OK`). 즉 이 pre-existing failure 는 dirty worktree 안에 이미 존재하던 것이고, 이번 seq 584 라운드가 새로 만든 regression 이 아님. 다만 seq 584 handoff 가 참고한 "143 prior + 1 new" 가정 자체가 dirty worktree baseline 기준이었고, 실제 dirty worktree 는 이 라운드 append 직전에 이미 145 total (144 pass + 1 fail) 였던 것으로 해석됨.
- `python3 -m py_compile tests/test_watcher_core.py` → exit 0 (`compile_ok`).
- `git diff --check -- work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall.md tests/test_watcher_core.py` → 출력 없음 (rc=0).
- `rg -n 'test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt|WatcherDispatchQueueControlMismatchTest' tests/test_watcher_core.py` → 3 히트: class def line 2143, skip decorator + def lines 2296–2297, evidence comment line 2298–2299. 기존 WatcherDispatchQueue 관련 테스트들은 그대로 유지.
- `python3 -c "...events.jsonl seq 236/245/423..."` → seq 236 / 245 `supervisor lane_working`, seq 423 `supervisor lane_ready`, timestamps 와 event_type 모두 `/work` 인용과 byte-exact.
- `ls .pipeline/runs/20260420T142213Z-p817639/receipts/` → 빈 디렉터리.
- wrapper-events/claude.jsonl 시간 창 필터 → `HEARTBEAT=50` (전체는 196 + 1 READY; 창 범위 외 나머지는 이번 주장 범위 밖).
- 실행하지 않은 항목 (명시):
  - `make e2e-test`, Playwright, `tests.test_web_app`: 이번 라운드가 브라우저/e2e 계약을 건드리지 않고 test-skeleton 수준이라 의도적 생략.
  - `tests.test_pipeline_runtime_supervisor` (101), `tests.test_pipeline_runtime_control_writers` (7), `tests.test_operator_request_schema` (6), `tests.test_pipeline_runtime_schema` (36), `tests.test_pipeline_gui_backend` (46): AXIS-G5 silent 유지 계약대로 이번 라운드 범위 밖.
  - full-repo dirty worktree audit: 범위 밖.

## 남은 리스크
- **AXIS-G4 trace captured, NOT fixed**: seq 584 라운드가 stall-trace note + skipped test skeleton 으로 boundary 를 `WatcherDispatchQueue` interaction 으로 이름 짓는 데 성공. 다음 G4 implement slice 는 또 다른 trace 가 아니라 actual fix 여야 함. 단, 현재 evidence 는 supervisor state write 와 wrapper event emit 중 어느 한쪽을 단정하지 않음 → 다음 fix slice 는 "어느 경계가 fix owner 인지" 부터 pin 필요.
- **pre-existing failure `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` (line 4654)**: 이 round 가 만든 regression 아님. HEAD 에서는 해당 테스트 존재하지 않음 (139 baseline). dirty worktree 안에서 prior round 가 추가한 테스트가 현재 assertion 과 실제 상태가 어긋난 상태로 남아 있음. 별도 slice 후보로 surface. 현재는 `.pipeline/claude_handoff.md` seq 584 범위 밖이라 이번 verify 에서 고치지 않음.
- **`/work` `## 검증` 본문 공란**: implement 라인이 명령을 돌리지 않았거나 수치를 옮기지 않은 채 닫은 상태. 이번 `/verify` 가 실제 재실행 결과를 이 노트의 `## 검증` 섹션에 채웠으므로 truth 갱신은 완료. `/work` 파일 본체 재편집은 이번 round 범위 밖(verify-owned 추가 편집은 scope 확장 위험).
- **G5 non-thin-client baselines 5종 (supervisor 101 / control_writers 7 / operator_request_schema 6 / schema 36 / watcher_core 143)**: 의도적으로 silent. 다만 `watcher_core` 쪽은 이번 재실행에서 실제 146 total / 144 pass 로 143 과 다름 — 이는 dirty worktree drift 의 일부이며 HEAD 139 green 과도 다름. G5 count bundle 자체는 여전히 의도적으로 pin 하지 않음.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: queue doc seq 576 materialized, trigger met 유지. verify-lane 실제 실행(`verify/4/20/2026-04-20-dispatcher-trace-backfill-verification.md`) 은 여전히 pending. 이번 verify 는 AXIS-G4 에 집중했으므로 그 큐 실행을 같은 round 에 겸하지 않음.
- **AXIS-G6-TEST-WEB-APP**: `tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError 그대로 열려 있음.
- **G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: deferred 유지.
- **Docs-only round count**: 오늘(2026-04-20) 2 그대로. 이번 라운드는 code/test 라 3+ saturation 경계 미촉발.
- **Canonical 계약 보존**: seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 / 564 / 567 / 570 / 576 / 581 byte-for-byte 유지. `.pipeline/operator_request.md` seq 521 canonical literals 는 SUPERSEDES chain 558 → 573 → 579 통해 그대로 보존.
- **다음 슬라이스 선택 모호성 → Gemini-first**: 후보가 서로 다른 축에 걸쳐 있고 current-risk dominance 가 뚜렷하지 않음.
  - (A) AXIS-G4 actual fix (fix owner 경계를 supervisor vs wrapper vs WatcherDispatchQueue 중 어디로 잡을지 Gemini pin 필요)
  - (B) `tests.test_watcher_core` pre-existing `test_blocked_triage_defers_until_codex_prompt_is_ready` failure 좁혀 닫기 (line 4654, dirty worktree 안)
  - (C) AXIS-G6-TEST-WEB-APP 단일 method 좁히기 (medium-high risk)
  - (D) verify-lane 이 queued AXIS-DISPATCHER-TRACE-BACKFILL 를 별도 verify 라운드로 실행 (implement slice 아님)
  real operator-only blocker 없음 → seq 585 next-control 은 `.pipeline/operator_request.md` 가 아니라 `.pipeline/gemini_request.md` 로 여는 것이 맞음.
- **Dirty worktree**: 이번 verify 가 새로 stage / reset 하지 않음. 기존 dirty 상태 그대로.
