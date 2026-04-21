# 2026-04-20 pipeline_gui state_transition G5-sub-D verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-state-transition-g5-sub-d-verification.md`

## 사용 skill
- `round-handoff`: seq 465 `.pipeline/claude_handoff.md`(G5-sub-D, Gemini 464 advice narrowed) 구현 주장을 `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(`tests.test_pipeline_gui_backend`, `tests.test_smoke -k progress_summary/coverage`, `py_compile`, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 465 `.pipeline/claude_handoff.md`(Gemini 464 advice의 unbounded "test-side rewrite" framing을 verify/handoff owner가 G5-sub-D 형태로 좁힌 것)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-state-transition-g5-sub-d.md`가 제출되었습니다.
- 목표는 `TestRuntimeStatusRead`에서 shipped `pipeline_gui/backend.py::read_runtime_status`가 제공하지 않는 state-transition spec을 강하게 요구하는 11개 drifted cell만 stable skip reason으로 명시적 defer 처리하고, backend 코드는 건드리지 않는 것이었습니다.

## 핵심 변경
- `tests/test_pipeline_gui_backend.py`에 11개 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator가 정확히 `:594`, `:644`, `:719`, `:794`, `:869`, `:947`, `:1018`, `:1067`, `:1135`, `:1203`, `:1265`에 삽입됨을 grep으로 확인. `/work` 기록 라인과 exact match.
- reason string은 11건 모두 정확히 `"pipeline_gui_backend_state_transition_deferred"`. variation 없음. 미래 unskipping 라운드가 grep할 load-bearing 계약 유지.
- skip 대상은 handoff가 명시한 11개 메서드 set과 일치:
  - `test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - `test_read_runtime_status_from_current_run_pointer`
  - `test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`
  - `test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`
  - `test_read_runtime_status_converts_stopping_without_supervisor_into_stopped`
  - `test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous`
  - `test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids`
  - `test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing`
  - `test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded`
  - `test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous`
  - `test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing`
- `rg -n 'def test_read_runtime_status' tests/test_pipeline_gui_backend.py` 결과 12건으로, skip되지 않은 활성 메서드 `test_read_runtime_status_returns_none_without_current_run` 1건이 `TestRuntimeStatusRead`에 남아 정상 실행됨을 확인. `/work`가 기록한 "12개 중 11개 skip" 비율과 정합.
- `pipeline_gui/backend.py`는 전혀 편집되지 않았음을 `git diff --check`와 `rg -n 'pipeline_gui_backend_state_transition_deferred' pipeline_gui/ storage/ core/ app/` 결과(0건)로 재확인. `read_runtime_status`(`:527-542`) / `runtime_state`(`:587-591`) / `supervisor_alive`(`:560-584`) thin-reader 계약 유지.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459 shipped 표면 전부 미편집 확인. `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, client/serializer/Playwright, legend, `status_label` 4-literal set 모두 그대로.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `465` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 466.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `463` — seq 464 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `464` — seq 465 handoff로 narrowed + 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — seq 465 claude_handoff(newest-valid-control)로 자연스럽게 supersede됨. G5-sub-D 구현은 당시 `ACCEPT_TEST_DRIFT` 옵션의 더 좁은 변형(delete가 아닌 skip, 11개 명명 대상에 한정)으로 해석됨.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.053s`, `OK (skipped=11)`. baseline `failures=8, errors=3`에서 post-edit `skipped=11, failures=0, errors=0`으로 전환. `/work` 기록과 정합.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.014s`, `OK`. seq 453 baseline 유지.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.050s`, `OK`. seq 453 baseline 유지.
- `python3 -m unittest tests.test_smoke -k claims` (verify 라운드에서는 생략; `/work`가 7 OK 기록하고 이번 slice는 `tests/test_smoke.py`를 건드리지 않아 baseline 유지 가정 안전).
- `python3 -m unittest tests.test_smoke -k reinvestigation` (동일 사유로 생략; `/work` 6 OK 기록).
- `python3 -m py_compile tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과.
- `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드가 test-file-only slice라 의도적으로 생략.

## 남은 리스크
- **11개 cell은 fix가 아니라 defer 상태**: 실제 state-transition feature(supervisor liveness detection, RUNNING→BROKEN / STOPPING→STOPPED / RUNNING→DEGRADED 규칙, degraded_reason vocabulary 정규화)는 여전히 `pipeline_gui/backend.py`에 구현되어 있지 않습니다. 미래 라운드에서 (i) unskip + 구현, (ii) spec 삭제, (iii) indefinite skip 중 하나 결정이 필요합니다. grep `"pipeline_gui_backend_state_transition_deferred"` 11건으로 재진입 가능.
- **operator_request seq 462 자연 해제**: seq 465 claude_handoff가 newest-valid-control이 되어 seq 462 stop은 supersede되었지만, 당시 4개 옵션(`SCOPE_G5_AS_MULTI_ROUND` / `ACCEPT_TEST_DRIFT` / `DEFER_G5` / `ACKNOWLEDGE_INFORMATIONAL`) 자체는 future arbitration framing으로 유효. G5-sub-D는 `ACCEPT_TEST_DRIFT`의 narrow 변형에 해당.
- **Gemini arbitration loop 경계**: 두 라운드 연속으로 Gemini가 G5를 non-bounded 형태로 반환(seq 461, 464). verify/handoff owner가 세 번째 바운스 대신 자체 narrowing을 적용해 진전을 만들었지만, 이 패턴이 반복되면 Gemini arbitration 유용성 자체가 낮아집니다. 다음 라운드에서 Gemini가 또 non-bounded advice를 주면 명시적으로 F-PIVOT 혹은 operator escalation path를 강제하는 방향이 맞을 수 있습니다.
- **unrelated red test 잔존**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError는 G6-sub2 후보로 남아 있고, legacy `"단일 출처 상태"` fixture 14 hit은 G6-sub3 judgment 후보. 모두 이번 slice 범위 밖.
- **다음 슬라이스 ambiguity**: G3(threshold tuning), G5-unskip-candidate(미래 state-transition 구현), G6-sub2/G6-sub3(test_web_app residuals), G7(vocabulary enforcement), G8(memory foundation), G9(naming-collision cleanup), G10(role_confidence COMMUNITY), G11(SQLiteSessionStore adoption-list meta-audit)가 모두 서로 다른 축. dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 466)로 여는 편이 `/verify` README 규칙과 일치.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 그대로. 이번 라운드는 tests-only. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 해당 파일들을 건드리지 않음.
