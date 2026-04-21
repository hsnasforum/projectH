# 2026-04-20 pipeline_gui helper unskip G5-AGED_AMBIGUOUS_BARE verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-aged-ambiguous-bare-verification.md`

## 사용 skill
- `round-handoff`: seq 486 `.pipeline/claude_handoff.md`(G5-unskip-AGED_AMBIGUOUS_BARE, Gemini 485 advice NARROWED) 구현 주장을 `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + 단일 unskip 테스트 direct rerun + `SNAPSHOT_STALE_THRESHOLD|parse_iso_utc` guard grep + `py_compile` + `git diff --check`을 직접 재실행했습니다.

## 변경 이유
- seq 486 `.pipeline/claude_handoff.md`(Gemini 485 advice를 verify/handoff owner가 narrowing)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-aged-ambiguous-bare.md`가 제출되었습니다.
- 목표는 `:1062` `@unittest.skip` 한 줄만 제거해 seq 480 RUNNING→BROKEN branch로 이미 커버되는 셀을 zero-backend-change로 활성화하고, advice 485의 age machinery + bifurcation 제안을 REJECT하는 것이었습니다.

## 핵심 변경
- `tests/test_pipeline_gui_backend.py:1062`(pre-edit) `@unittest.skip` 한 줄 삭제 확인.
- 남은 4개 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator는 정확히 `:942, :1013, :1196, :1258` 위치에 있음 — `/work` 기록과 exact match. `:942, :1013`은 이전 위치 그대로(해당 라인은 삭제된 `:1062` 이전이라 shift 없음), `:1196, :1258`은 `:1197, :1259`에서 한 줄씩 up shift.
- `pipeline_gui/backend.py` 완전 비편집 확인. `SNAPSHOT_STALE_THRESHOLD`, `parse_iso_utc` 모두 0건 hit으로 advice 485의 age machinery 제안이 실제로 도입되지 않았음을 grep으로 최종 확인.
- 6개 previously-unskipped cells(seq 483/480/477/474/471/468) 모두 green 유지 확인 (baseline skipped=5 → post-edit skipped=4, 새 failures/errors 0).
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483 shipped surfaces 전부 미편집. `git diff --check` 0건.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `486` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 487.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `484` — seq 485 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `485` — seq 486 handoff로 narrowed + 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.052s`, `OK (skipped=4)`. baseline `OK (skipped=5)` → post-edit `OK (skipped=4)`. 새 failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`
  - 결과: `Ran 1 test in 0.004s`, `OK`. unskipped 셀 zero-backend-change로 clean pass.
- skip decorator grep: 정확히 4건(`:942, :1013, :1196, :1258`).
- `SNAPSHOT_STALE_THRESHOLD|parse_iso_utc` grep in pipeline_gui/backend.py: 0건 — advice 485 age machinery가 실제로 도입되지 않았음을 확인.
- `python3 -m py_compile tests/test_pipeline_gui_backend.py pipeline_gui/backend.py` → 출력 없음, 통과.
- `git diff --check -- tests/test_pipeline_gui_backend.py pipeline_gui/backend.py` → 출력 없음, 통과.
- `-k progress_summary/coverage/claims/reinvestigation`는 `/work`가 각 11/27/7/6 OK 기록, 이번 slice가 `tests/test_smoke.py`/`pipeline_gui/backend.py`/`core/`/`app/`/`storage/`를 건드리지 않아 baseline 유지 안전. verify 재실행 생략.
- `tests.test_web_app`, Playwright, `make e2e-test`는 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **4 cells 여전히 deferred**:
  - `:942` `recent_field_quiescent_running_status_broken_without_pids` — lane-preservation logic 필요. fixture는 lane state="OFF"를 보존해야 하지만 seq 480 rule이 "BROKEN"으로 강제 rewrite. 다음 라운드에서 (i) seq 480을 narrow해 quiescent lane일 때 state 보존, OR (ii) 더 앞에 별도 branch 추가 선택 필요.
  - `:1013` `recent_active_lane_without_supervisor_pid_degraded_ambiguous` — DEGRADED 기대, seq 480 broad RUNNING→BROKEN rule과 충돌
  - `:1196` `undated_ambiguous_snapshot_degraded` — DEGRADED, 충돌
  - `:1258` `watcher_only_alive_without_pid_degraded_ambiguous` — DEGRADED, 충돌
- **DEGRADED family collision 미해결**: `:1013, :1196, :1258`는 supervisor_missing이면 seq 480 RUNNING→BROKEN branch에 먼저 잡혀 BROKEN 반환 예상. unskip 시 반드시 DEGRADED branch를 RUNNING→BROKEN 앞에 더 narrow한 trigger로 삽입 필요.
- **advice 485 age-bifurcation 기록**: 이번 라운드에서 REJECT됐지만, DEGRADED-family에서 정말 age-based differentiation이 필요한 fixture를 발견하면 그때 재검토 가능. 단 반드시 각 DEGRADED test fixture를 개별 inspection한 뒤 결정.
- **branch duplication 3개**: STOPPING + BROKEN + RUNNING→BROKEN + quiescent. G12 shared helper refactor는 4번째 유사 분기 추가 시 검토.
- **다음 슬라이스 ambiguity**: 4 G5-unskip-* 후보 + G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11 / G12가 서로 다른 축이고 dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 487)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 targeted 1 file 외 변경 없음.
