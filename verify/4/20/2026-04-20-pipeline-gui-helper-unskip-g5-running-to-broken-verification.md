# 2026-04-20 pipeline_gui helper unskip G5-RUNNING_TO_BROKEN verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-running-to-broken-verification.md`

## 사용 skill
- `round-handoff`: seq 480 `.pipeline/claude_handoff.md`(G5-unskip-RUNNING_TO_BROKEN, Gemini 479 advice) 구현 주장을 `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + 5개 targeted regression(신규 STALE + seq 477/474/471/468 unskip), `py_compile`, `git diff --check`을 직접 재실행했습니다.

## 변경 이유
- seq 480 `.pipeline/claude_handoff.md`(Gemini 479 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-running-to-broken.md`가 제출되었습니다.
- 목표는 `supervisor_missing` 판정을 PID-file 존재에서 PID liveness로 넓히고 `supervisor_missing AND runtime_state == "RUNNING"` 조건에 해당하는 새 branch를 seq 477 BROKEN branch 바로 뒤에 추가해 `test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing`만 unskip하는 것이었습니다.

## 핵심 변경
- `pipeline_gui/backend.py:90` `supervisor_missing = project is not None and not supervisor_alive(project)[0]`로 widen됨 — missing pid file뿐 아니라 pid exists but dead-process(zombie) case도 같은 semantic으로 잡힘. Python은 name lookup을 call-time에 하므로 `supervisor_alive`가 아래(`:619+` 인근)에서 정의돼도 정상 해결됨.
- `:91-113` seq 474 STOPPING branch 미변경(`"note": "stopped"` 1건 at `:109`, lane `state="OFF"`).
- `:114-135` seq 477 BROKEN branch 미변경(`"note": "supervisor_missing"` at `:131`, lane `state="BROKEN"`, runtime_state 비변경).
- `:136-158` 신규 RUNNING→BROKEN branch 확인:
  - `:136` guard `if supervisor_missing and runtime_state == "RUNNING":`
  - `:137` `status["runtime_state"] = "BROKEN"` **FLIP from RUNNING** — 핵심 차이. seq 477 BROKEN branch는 runtime_state를 수정하지 않았지만 이 branch는 flip.
  - `:138-147` degraded_reason/degraded_reasons/control/active_round/watcher 재작성 — seq 477과 동일.
  - `:148-157` lanes rewrite with `state="BROKEN"`, `attachable=False`, `pid=None`, `note="supervisor_missing"` — seq 477과 동일.
  - `:158` early return.
- `:159+` 기존 quiescent block 미변경 확인.
- `"note": "supervisor_missing"` 리터럴은 이제 2건(`:131` BROKEN, `:154` RUNNING→BROKEN). `"note": "stopped"`는 1건(`:109` STOPPING) 유지.
- `tests/test_pipeline_gui_backend.py`의 `:643` skip decorator 제거 확인. 남은 6개는 handoff가 예측한 한 줄 shift된 `:865, :943, :1014, :1063, :1198, :1260` 위치.
- 4개 previously-unskipped cell(seq 468/471/474/477) direct rerun 결과 모두 green 유지 확인 — `supervisor_missing` widening 영향 zero-risk 입증.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477 shipped 표면 전부 미편집 확인. `git diff --check` 0건.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `480` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 481.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `478` — seq 479 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `479` — seq 480 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.064s`, `OK (skipped=6)`. baseline `OK (skipped=7)` → post-edit `OK (skipped=6)`. 새 failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.{test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing, test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing, test_read_runtime_status_converts_stopping_without_supervisor_into_stopped, test_read_runtime_status_from_current_run_pointer, test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive}`
  - 결과: `Ran 5 tests in 0.016s`, `OK`. 신규 STALE cell + seq 477/474/471/468 regression 전부 green.
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과.
- `-k progress_summary/coverage/claims/reinvestigation`는 `/work`가 각 11/27/7/6 OK로 기록했고, 이번 slice는 `tests/test_smoke.py` / `core/` / `app/` / `storage/`를 건드리지 않아 baseline 유지 안전. verify 재실행 생략.
- `tests.test_web_app`, Playwright, `make e2e-test`는 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **6 cells 여전히 deferred**: `TestRuntimeStatusRead` 6개 cell은 여전히 `@unittest.skip`. 남은 sub-family 매핑:
  - `:865` `recent_quiescent_running_status_broken_without_supervisor` — 새 blanket RUNNING→BROKEN rule이 이미 이 case를 catch할 가능성이 있으므로 다음 라운드는 assertion 검증만으로 unskip 가능할 수 있음. 확인 필요.
  - `:943` `converts_aged_ambiguous_snapshot_into_broken` — age-based trigger 필요
  - `:1014` `recent_field_quiescent_running_status_broken_without_pids` — field-level quiescence + no pids
  - `:1063` `recent_active_lane_without_supervisor_pid_degraded_ambiguous` — DEGRADED 기대, **새 RUNNING→BROKEN rule이 충돌**
  - `:1198` `undated_ambiguous_snapshot_degraded` — DEGRADED 기대, **충돌**
  - `:1260` `watcher_only_alive_without_pid_degraded_ambiguous` — DEGRADED 기대, **충돌**
- **DEGRADED family collision 확정**: 새 blanket RUNNING→BROKEN rule이 `:1063/:1198/:1260`의 DEGRADED-family fixture에서 supervisor_missing이 True면 먼저 발화해 BROKEN을 반환할 것. 셋 다 skip 상태라 이번 라운드는 무해하지만, future DEGRADED-family unskip 슬라이스는 **반드시 RUNNING→BROKEN branch 앞에 더 좁은 DEGRADED branch**를 배치해 recent-active-lane / undated / watcher-only-alive signal로 구분해야 합니다. handoff와 `/work` 모두 이 설계 제약을 명시하고 있어 투명성 유지됨.
- **branch duplication 3개 도달**: STOPPING + BROKEN + RUNNING→BROKEN 세 유사-형태 branch. 4번째 동형 branch가 추가되면 `_apply_shutdown_shape(status, lanes, *, runtime_state_override, lane_state, lane_note, degraded_reason, degraded_reasons)` 도입 검토. 이번 라운드는 의도적 비도입.
- **다음 슬라이스 ambiguity**: 6 G5-unskip-* 후보 + G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11 이 모두 서로 다른 축. dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 481)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests 잔존**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 targeted 2 files 외 변경 없음.
