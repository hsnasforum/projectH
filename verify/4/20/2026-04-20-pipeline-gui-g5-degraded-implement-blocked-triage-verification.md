# 2026-04-20 pipeline_gui G5 DEGRADED implement_blocked triage verification

## 변경 파일
- `pipeline_gui/backend.py` (seq 492 partial edit revert)
- `tests/test_pipeline_gui_backend.py` (seq 492 partial edit revert)
- `.pipeline/gemini_request.md` (CONTROL_SEQ: 493, re-arbitration open)
- `verify/4/20/2026-04-20-pipeline-gui-g5-degraded-implement-blocked-triage-verification.md` (본 파일)

## 사용 skill
- `round-handoff`: seq 492 `.pipeline/claude_handoff.md`(G5-unskip-DEGRADED_NO_WATCHER, verify/handoff owner가 advice 491에서 narrow down한 cell-specific trigger) 구현 주장을 실제 코드/테스트 상태와 대조했고, `python3 -m unittest tests.test_pipeline_gui_backend` + targeted 재실행 + `py_compile`을 직접 재실행했으며, implementer의 `implement_blocked` sentinel(`BLOCK_REASON: aged_ambiguous_regression` / `BLOCK_REASON_CODE: verification_failure`)을 closing control로 변환했습니다.

## 변경 이유
- seq 492 `.pipeline/claude_handoff.md`가 `STATUS: implement`로 implementer에게 전달됐고, implementer는 편집 일부를 적용한 뒤 verification에서 regression을 검출해 `implement_blocked` sentinel을 반환했습니다.
- 목표: 이번 triage 라운드에서 (a) seq 492 부분 편집이 실제로 regression을 일으켰는지 재실행으로 확인, (b) 원인(age discriminator 부재)을 empirical evidence로 pin down, (c) worktree를 seq 489 baseline으로 복구, (d) next control을 Gemini arbitration으로 열기.

## 핵심 변경
- seq 492 handoff는 advice 491의 unified 3-cell DEGRADED 제안에서 "1 cell + narrow cell-specific trigger + age machinery 거부"로 narrow down했으나, `:1012` recent DEGRADED와 `:1062` aged BROKEN 사이 collision을 놓쳤습니다. 두 fixture 모두 `supervisor_missing AND runtime_state=="RUNNING" AND not watcher.get("alive") AND lanes[0].state=="READY"`를 공유하고, 오직 `time.time` mock(`+10.0s` vs `+20.0s`)만 차이가 납니다.
- 실제 implementer 편집을 재검증한 결과:
  - `pipeline_gui/backend.py:136-143`에 새 narrow DEGRADED branch가 실제로 삽입됐고 (git diff에서 8줄 추가 확인),
  - `tests/test_pipeline_gui_backend.py:1012`의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 한 줄이 실제로 제거됐습니다.
  - `python3 -m unittest tests.test_pipeline_gui_backend` 재실행 결과: `Ran 45 tests in 0.074s` / `FAILED (failures=1, skipped=2)`, failure가 `test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken` (:1062, seq 486 shipped green)에서 `AssertionError: 'DEGRADED' != 'BROKEN'`.
  - implementer의 `implement_blocked` + `BLOCK_REASON: aged_ambiguous_regression` / `BLOCK_REASON_CODE: verification_failure` 판단 정확. verify/handoff owner seq 492의 narrowing 분석("there's only one test with this fixture shape in the current suite")은 오류 — `:1062`가 바로 그 aged counterpart였습니다.
- seq 493 triage revert:
  - `pipeline_gui/backend.py:136-143` (새 narrow DEGRADED branch 8줄) 제거해 seq 489 post-edit 상태로 복구.
  - `tests/test_pipeline_gui_backend.py:1012` 위에 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 복원해 seq 489 skip=3 baseline으로 복구.
  - 복구 후 재실행: `python3 -m unittest tests.test_pipeline_gui_backend` → `Ran 45 tests in 0.079s` / `OK (skipped=3)`.
- `.pipeline/gemini_request.md` CONTROL_SEQ 490 → 493로 갱신, `STATUS: request_open` 유지. 기존 candidate 구조 유지하되 empirical evidence 섹션 추가:
  - `:1012` vs `:1062` 공유 signal 전부 enumerate
  - 가능한 discriminator 후보: `snapshot_age` (clean, 15s threshold), `control` 필드 존재 여부, `active_round` 필드 존재 여부, `watcher` 원본 shape 존재 여부 — 마지막 셋은 brittle 평가
  - 새 candidate `G5-unskip-DEGRADED_WITH_AGE-MACHINERY` (advice 491의 age 부분을 1-cell 슬라이스로 축소) + `G5-unskip-DEGRADED_ALTERNATE-DISCRIMINATOR` (비-age signal 제안 요청) + 기존 `G12` refactor 옵션
  - tie-break: age machinery 선호, `:1062 aged_ambiguous`는 반드시 BROKEN 유지가 regression assertion에 포함됨
- `.pipeline/claude_handoff.md`는 CONTROL_SEQ 492 그대로. 새 handoff는 Gemini advice 493 도착 후에만 쓰는 편이 규칙에 부합 (next-slice design ambiguity → gemini_request가 operator_request보다 먼저).
- `.pipeline/operator_request.md`는 STATUS `needs_operator` / CONTROL_SEQ 462 그대로. real operator-only decision, approval/truth-sync blocker, immediate safety stop, Gemini unavailable/inconclusive 중 어느 것도 해당 안 되므로 갱신하지 않습니다.
- `.pipeline/gemini_advice.md` CONTROL_SEQ 491 stale. 이번 라운드에서 덮어쓰지 않습니다 (Gemini의 다음 응답이 seq 493 advice로 새로 쓰임).

## 검증
- `python3 -m unittest tests.test_pipeline_gui_backend` (revert 전)
  - 결과: `Ran 45 tests in 0.074s`, `FAILED (failures=1, skipped=2)`
  - failure: `test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken` at `:1062`, `AssertionError: 'DEGRADED' != 'BROKEN'`
- `python3 -m unittest tests.test_pipeline_gui_backend` (revert 후)
  - 결과: `Ran 45 tests in 0.079s`, `OK (skipped=3)`
  - baseline transition: seq 492 partial state `FAILED (failures=1, skipped=2)` → seq 493 revert `OK (skipped=3)`, seq 489 baseline 재확인.
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `.pipeline` rolling slot snapshot (triage 마감 시점)
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `492` — 소비됐고 implementer sentinel로 닫힘, 다음 implement는 seq 494+ (Gemini 493 advice 도착 후).
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `493` — 이번 triage가 새로 열음.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `491` — seq 492 narrowing이 일부 참고, 이제 stale. Gemini 493 응답이 덮어쓰게 됨.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded, 이번 triage는 operator escalation이 아니므로 그대로.
- `tests.test_smoke -k progress_summary/coverage/claims/reinvestigation`, `tests.test_web_app`, Playwright, `make e2e-test`는 이번 triage 범위 밖이라 의도적으로 생략. seq 492 partial 편집이 이 경로들을 건드리지 않았기에 seq 489 baseline과 동일 가정이 안전 (revert 이후라 더 강하게 성립).

## 남은 리스크
- **3 DEGRADED cells 여전히 deferred** (seq 489 baseline 그대로):
  - `:1012` `recent_active_lane_without_supervisor_pid_degraded_ambiguous`
  - `:1195` `undated_ambiguous_snapshot_degraded`
  - `:1257` `watcher_only_alive_without_pid_degraded_ambiguous`
- **DEGRADED collision empirical 확인**: `:1012` vs `:1062`는 `watcher.alive falsy + RUNNING + lane READY + supervisor_missing`을 전부 공유하고 `snapshot_age`만 달라짐. age 이외의 clean discriminator를 찾지 못하면 `parse_iso_utc` 기반 age machinery가 사실상 필수. 다음 라운드에서 Gemini가 재arbitrate.
- **advice 491 부분 복권 필요**: verify/handoff owner seq 492의 "age machinery 불필요" 결론은 empirical evidence로 반박됐습니다. Gemini 493 응답은 age machinery 재도입(1 cell + `SNAPSHOT_STALE_THRESHOLD = 15.0`) 또는 더 나은 non-age discriminator 둘 중 하나를 pin down 해야 합니다.
- **normalize_runtime_status 분기 수**: revert 이후 STOPPING + BROKEN + RUNNING→BROKEN + quiescent 4개 유지. DEGRADED 추가 시 5개로 증가. G12 `_apply_shutdown_shape` refactor의 leverage는 이번 block으로 오히려 증가했습니다 — 같은-모양 분기 추가 직전에 refactor를 검토하는 편이 합리적.
- **seq 492 verify/handoff owner 분석 결함 lesson**: "해당 fixture shape의 유일한 test"라고 주장하기 전에 같은 family의 모든 cell을 전수 스캔해야 함. `:1062` 같은 shipped-green regression counterpart를 놓치면 narrow trigger가 regression을 일으킵니다. 다음 narrow-trigger 제안은 해당 supervisor_missing + RUNNING branch를 공유하는 모든 currently-green cell의 fixture shape를 비교표로 pin 해야 합니다.
- **unrelated red tests**: `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 triage는 seq 492 partial 편집 revert 2건 + `.pipeline/gemini_request.md` 갱신 + 이 verify 노트 외 변경 없습니다.
