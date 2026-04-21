# 2026-04-20 pipeline_gui helper unskip G5-DEGRADED_REASON verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-degraded-reason-verification.md`

## 사용 skill
- `round-handoff`: seq 477 `.pipeline/claude_handoff.md`(G5-unskip-DEGRADED_REASON, Gemini 476 advice) 구현 주장을 `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + 4개 targeted regression(신규 DEGRADED_REASON + seq 474/471/468 unskip), `py_compile`, `git diff --check`을 직접 재실행했습니다.

## 변경 이유
- seq 477 `.pipeline/claude_handoff.md`(Gemini 476 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-degraded-reason.md`가 제출되었습니다.
- 목표는 seq 474의 STOPPING branch 직후에 parallel BROKEN branch(runtime_state 불변 유지, diagnostic fields + lanes normalize)를 추가하고 `test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing`를 unskip하는 것이었습니다.

## 핵심 변경
- `pipeline_gui/backend.py:114-135` 신규 BROKEN branch 실제 상태
  - `:114` guard `if supervisor_missing and runtime_state == "BROKEN":` — seq 474 STOPPING branch(`:91-113`) return 직후에 삽입, seq 474 quiescent block(`:136+`) 직전 위치로 handoff 지시와 exact match.
  - `:115-116` `degraded_reason = "supervisor_missing"`, `degraded_reasons = ["supervisor_missing"]` 재작성으로 raw `"auth_login_required"` 덮어쓰기.
  - `:117-122` control을 `{"", -1, "none", ""}` 스키마로 reset.
  - `:123` `active_round = None`.
  - `:124` `watcher = {"alive": False, "pid": None}` — 원본 `watcher.alive: True` 강제 덮어쓰기.
  - `:125-134` 각 lane에 대해 `state = "BROKEN"`, `attachable = False`, `pid = None`, `note = "supervisor_missing"` 강제. **`runtime_state`는 변경하지 않고 "BROKEN" 그대로 유지** — handoff의 핵심 narrowing 포인트.
  - `:135` early return.
- 기존 STOPPING branch(`:91-113`)와 quiescent block(`:136-163`) 미변경 확인. `"note": "stopped"` 1건 (`:109`)이 STOPPING branch에만, `"note": "supervisor_missing"` 1건 (`:131`)이 BROKEN branch에만 존재 — handoff의 duplicate-then-vary 원칙 유지.
- `tests/test_pipeline_gui_backend.py:792` skip decorator 한 줄 제거 확인. 남은 7개 skip decorator는 `:643, :866, :944, :1015, :1064, :1199, :1261` 위치로, handoff가 예측한 shift(이전 `:643, :867, :945, :1016, :1065, :1200, :1262`에서 한 줄 up shift)와 exact match.
- seq 468/471/474 unskip된 세 regression test 모두 BROKEN branch 추가 이후에도 green 유지 확인. 이들은 runtime_state가 각각 RUNNING/RUNNING/STOPPING이라 새 BROKEN branch 비발화, STOPPING branch는 독립적으로 동작.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474 shipped 표면 전부 미편집 확인. `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, client/serializer/Playwright 모두 그대로. `git diff --check` 0건.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `477` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 478.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `475` — seq 476 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `476` — seq 477 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.044s`, `OK (skipped=7)`. baseline `OK (skipped=8)` → post-edit `OK (skipped=7)`. 새 failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.{test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing, test_read_runtime_status_converts_stopping_without_supervisor_into_stopped, test_read_runtime_status_from_current_run_pointer, test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive}`
  - 결과: `Ran 4 tests in 0.010s`, `OK`. 신규 DEGRADED_REASON cell + seq 474/471/468 regression 모두 green.
- grep 검증
  - `rg -n '"note": "supervisor_missing"' pipeline_gui/backend.py` → 1건 (`:131`)
  - `rg -n '"note": "stopped"' pipeline_gui/backend.py` → 1건 (`:109`) — STOPPING branch에 유지
  - `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py` → 7건 (예상치 정합)
  - `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py` → 7건
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `-k progress_summary/coverage/claims/reinvestigation`는 `/work`가 각 11/27/7/6 OK로 기록했고, 이번 slice는 `tests/test_smoke.py` / `core/` / `app/` / `storage/`를 건드리지 않아 baseline 유지가 안전. verify 재실행 생략.
- `tests.test_web_app`, Playwright, `make e2e-test`는 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **7 cells 여전히 deferred**: `TestRuntimeStatusRead`의 7개 cell은 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 상태. future G5-unskip-* sub-family 중 state-transition 규칙이 필요한 것들이 남았고, 일부는 snapshot-age 계산 같은 새 helper가 필요할 수 있습니다. 다음 이름 매핑:
  - `:643` — stale_RUNNING_BROKEN (RUNNING→BROKEN with staleness)
  - `:866` — recent_quiescent_running_BROKEN (RUNNING→BROKEN recent quiescent without supervisor)
  - `:944` — aged_ambiguous_BROKEN (RUNNING→BROKEN aged ambiguous)
  - `:1015` — recent_field_quiescent_running_BROKEN (RUNNING→BROKEN recent_field_quiescent without pids)
  - `:1064` — recent_active_lane_DEGRADED (RUNNING→DEGRADED recent active lane without supervisor_pid)
  - `:1199` — undated_ambiguous_DEGRADED (RUNNING→DEGRADED undated ambiguous)
  - `:1261` — watcher_only_alive_DEGRADED (RUNNING→DEGRADED watcher_only_alive without pid)
- **normalize_runtime_status branch duplication 누적**: STOPPING + BROKEN + quiescent 세 유사 블록 구조. 다음 G5-unskip-* 진행에서 세 번째 동형 패턴이 확인되면 shared helper `_apply_shutdown_shape(status, lanes, *, runtime_state_override, lane_state, lane_note)` 도입 검토. 이번 라운드는 의도적으로 도입 안 함.
- **lane note 비대칭**: STOPPING(`"stopped"`) vs BROKEN(`"supervisor_missing"`) 리터럴이 다름. 각 branch의 post-normalization intent를 반영하므로 현재 테스트 기대값과 정합.
- **다음 슬라이스 ambiguity**: 남은 G5-unskip-* 7 후보 + G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11가 모두 서로 다른 축이고 dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 478)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests 잔존**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 그대로.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 targeted 2 files 외 변경 없음.
