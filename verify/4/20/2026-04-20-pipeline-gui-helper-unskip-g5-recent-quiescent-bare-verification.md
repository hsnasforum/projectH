# 2026-04-20 pipeline_gui helper unskip G5-RECENT_QUIESCENT_BARE verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-recent-quiescent-bare-verification.md`

## 사용 skill
- `round-handoff`: seq 483 `.pipeline/claude_handoff.md`(G5-unskip-RECENT_QUIESCENT_BARE, Gemini 482 advice) 구현 주장을 `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + 단일 unskip 테스트 direct rerun, `py_compile`, `git diff --check`을 직접 재실행했습니다.

## 변경 이유
- seq 483 `.pipeline/claude_handoff.md`(Gemini 482 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-recent-quiescent-bare.md`가 제출되었습니다.
- 목표는 `tests/test_pipeline_gui_backend.py:865`의 `@unittest.skip` 한 줄만 제거해 seq 480 RUNNING→BROKEN branch가 이미 커버하는 셀을 zero-backend-change로 활성화하는 것.

## 핵심 변경
- `tests/test_pipeline_gui_backend.py:865`(pre-edit)는 이제 `def test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor(self) -> None:`로 시작(`@unittest.skip` 한 줄 삭제 확인).
- `pipeline_gui/backend.py` 전혀 편집 안 함. seq 480 RUNNING→BROKEN branch가 test의 13개 assertion을 전부 자동으로 만족.
- 남은 5개 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator 위치는 정확히 `:942, :1013, :1062, :1197, :1259` — `/work` 기록과 exact match. 기존 `:943, :1014, :1063, :1198, :1260`에서 한 줄씩 shifted up.
- seq 480 / 477 / 474 / 471 / 468 previously-unskipped cells 모두 green 유지 확인 (baseline skipped=6 → post-edit skipped=5, 새 failures/errors 0).
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480 shipped surfaces 전부 미편집. `git diff --check` 0건.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `483` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 484.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `481` — seq 482 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `482` — seq 483 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.064s`, `OK (skipped=5)`. baseline `OK (skipped=6)` → post-edit `OK (skipped=5)`. 새 failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`
  - 결과: `Ran 1 test in 0.004s`, `OK`. unskipped 셀 zero-backend-change로 clean pass.
- `python3 -m py_compile tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `git diff --check -- tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- skip decorator grep: 정확히 5건(`:942, :1013, :1062, :1197, :1259`), backend/storage/core/app에는 0건(skip reason 테스트 파일 전용).
- `-k progress_summary/coverage/claims/reinvestigation`는 `/work`가 각 11/27/7/6 OK 기록, 이번 slice가 `tests/test_smoke.py`/`pipeline_gui/backend.py`/`core/`/`app/`/`storage/`를 건드리지 않아 baseline 유지 안전. verify 재실행 생략.
- `tests.test_web_app`, Playwright, `make e2e-test`는 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **5 cells 여전히 deferred**: `TestRuntimeStatusRead`의 5개 cell은 `@unittest.skip` 상태. 남은 sub-family 매핑:
  - `:942` `converts_aged_ambiguous_snapshot_into_broken` — age-based trigger 필요
  - `:1013` `recent_field_quiescent_running_status_broken_without_pids` — seq 480 rule로 이미 커버될 가능성 있음; 다음 라운드에서 assertion inspection 후 decorator-only unskip 가능성
  - `:1062` `recent_active_lane_without_supervisor_pid_degraded_ambiguous` — DEGRADED 기대, seq 480 broad rule과 충돌
  - `:1197` `undated_ambiguous_snapshot_degraded` — DEGRADED, 충돌
  - `:1259` `watcher_only_alive_without_pid_degraded_ambiguous` — DEGRADED, 충돌
- **DEGRADED family collision 미해결**: `:1062/:1197/:1259`의 DEGRADED 셀들이 supervisor_missing + RUNNING이면 seq 480 broad rule에 먼저 잡혀 BROKEN을 반환할 것. 현재 skip 상태라 무해하지만 unskip 시 반드시 DEGRADED branch를 RUNNING→BROKEN branch 앞에 더 narrow한 trigger로 삽입 필요.
- **branch duplication 3개**: STOPPING + BROKEN + RUNNING→BROKEN + quiescent. G12 shared helper refactor가 4번째 유사 분기 추가 시 검토 대상.
- **다음 슬라이스 ambiguity**: 5 G5-unskip-* 후보 + G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11 / G12가 서로 다른 축이고 dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 484)로 여는 편이 `/verify` README 규칙과 일치.
- **`:1013` decorator-only 가능성**: seq 480 rule이 `:865` 케이스를 이미 cover하는 패턴이 반복되면, `:1013` `recent_field_quiescent_running_status_broken_without_pids`도 비슷하게 decorator-only unskip이 가능할 수 있음. 다음 라운드 우선 inspection 후보.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 targeted 1 file 외 변경 없음.
