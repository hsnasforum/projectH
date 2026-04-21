# 2026-04-20 pipeline_gui helper unskip G5-thin-reader verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-thin-reader-verification.md`

## 사용 skill
- `round-handoff`: seq 471 `.pipeline/claude_handoff.md`(G5-unskip-thin-reader, Gemini 470 advice narrowed) 구현 주장을 `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(전체 `tests.test_pipeline_gui_backend`, 단일 unskip 테스트 직접, grep 4종, `py_compile`, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 471 `.pipeline/claude_handoff.md`(Gemini 470 advice narrowed to G5-unskip-thin-reader)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-thin-reader.md`가 제출되었습니다.
- 목표는 `tests/test_pipeline_gui_backend.py:594`의 `@unittest.skip` 한 줄만 삭제해 thin-reader-covered cell `test_read_runtime_status_from_current_run_pointer`를 활성화하고, `pipeline_gui/backend.py`는 전혀 건드리지 않는 것이었습니다. 진짜 state-transition wiring은 계속 deferred.

## 핵심 변경
- `tests/test_pipeline_gui_backend.py:594`가 이제 `def test_read_runtime_status_from_current_run_pointer(self) -> None:`로 시작함(이전 `@unittest.skip` 라인 삭제됨). 직접 읽어 확인.
- test body(`:595-637`) 미변경. `_supervisor_pid` / `_pid_is_alive` mock.patch도 seq 468에서 노출된 module-level helpers 덕분에 정상 작동해 raw-JSON pass-through assertion이 clean pass.
- 남은 9개 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator는 `:643, :718, :793, :868, :946, :1017, :1066, :1201, :1263`에 위치. `/work` 기록과 정확히 일치하며, seq 471 handoff가 예측한 한 줄 shift(`:644→:643` 등) 결과와 정합.
- `pipeline_gui/backend.py` 비편집 확인. `_supervisor_pid`(`:560-577`), `_pid_is_alive`(`:580-589`), `supervisor_alive`(`:592-599`), `read_runtime_status`(`:527-542`), `runtime_state`(`:602-606`) 그대로. `git diff --check` 0건.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468 shipped 표면 전부 미편집. `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, client/serializer/Playwright 모두 그대로.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `471` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 472.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `469` — seq 470 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `470` — seq 471 handoff로 narrowed + 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — seq 465 이후 지속 superseded.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.035s`, `OK (skipped=9)`. baseline `OK (skipped=10)` → post-edit `OK (skipped=9)`. 새 failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer`
  - 결과: `Ran 1 test in 0.003s`, `OK`. unskipped 셀 clean pass.
- grep 검증
  - `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py` → 9건 (post-edit, 예상치 정합)
  - `pipeline_gui/`, `storage/`, `core/`, `app/`에는 0건 (skip reason이 테스트 파일에만 존재)
- `python3 -m py_compile tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `git diff --check -- tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `-k progress_summary / coverage / claims / reinvestigation`는 `/work`가 각 11/27/7/6 OK로 기록했고, 이번 slice가 `tests/test_smoke.py`를 건드리지 않아 baseline 유지가 안전하게 추정됨. verify 단계에서는 pipeline_gui_backend 두 실행으로 충분히 다룸.
- `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **9 cells deferred 유지**: `TestRuntimeStatusRead`의 나머지 9개 cell은 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")`로 남아 있고, 각각 state-transition feature를 인코딩합니다. 후속 G5-unskip-* 라운드가 sub-family 단위(STOPPING→STOPPED, RUNNING→BROKEN, RUNNING→DEGRADED, degraded_reason vocabulary)로 bounded slice로 나눠 풀 수 있지만, 각 unskip에는 `read_runtime_status` wiring이 함께 필요합니다.
- **advice label drift 기록됨**: Gemini 470이 "G5-unskip-B" 라벨을 seq 469 menu의 STOPPING→STOPPED state-transition rule과 다른 의미로 사용. `/work`가 이 차이를 투명하게 기록해 G5-unskip-thin-reader로 재명명. 다음 Gemini arbitration 라운드에서 menu의 라벨 정의와 advice 라벨을 정확히 매칭하는지 주목.
- **다음 슬라이스 ambiguity**: G5-unskip-B(STOPPING→STOPPED 실제 transition rule) / G5-unskip-C(degraded_reason vocabulary) / G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11이 모두 서로 다른 축이고 dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 472)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests 잔존**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로. G6-sub2 후보 유지.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 그대로. test-file-only slice라 docs drift 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 해당 파일들을 건드리지 않음.
