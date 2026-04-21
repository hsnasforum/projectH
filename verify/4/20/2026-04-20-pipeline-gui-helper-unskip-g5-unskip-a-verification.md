# 2026-04-20 pipeline_gui helper unskip G5-unskip-A verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-unskip-a-verification.md`

## 사용 skill
- `round-handoff`: seq 468 `.pipeline/claude_handoff.md`(G5-unskip-A, Gemini 467 advice) 구현 주장을 `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(전체 `tests.test_pipeline_gui_backend`, 단일 unskip 테스트 직접, `tests.test_smoke -k progress_summary/coverage/claims/reinvestigation`, `py_compile`, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 468 `.pipeline/claude_handoff.md`(Gemini 467 advice 기반 G5-unskip-A)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-unskip-a.md`가 제출되었습니다.
- 목표는 `supervisor_alive`를 `_supervisor_pid` + `_pid_is_alive` 두 module-level helper로 분리해 semantic no-op refactor를 수행하고, 이미 mock.patch-ready한 thin-reader assertion만 쓰는 1개 cell(`test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`)을 unskip하는 것이었습니다. `read_runtime_status` state-transition wiring은 이번 라운드에서 추가하지 않음.

## 핵심 변경
- `pipeline_gui/backend.py:560-599` refactor 실제 상태
  - `:560-577` 신규 `_supervisor_pid(project: Path) -> int | None` — Windows `cat`/parse + Linux `Path.read_text`/parse 두 경로 모두 원본 semantics 보존 확인.
  - `:580-589` 신규 `_pid_is_alive(pid: int) -> bool` — Windows `kill -0` / Linux `os.kill(pid, 0)` 두 경로 원본 semantics 보존 확인.
  - `:592-599` reduced `supervisor_alive(project)` wrapper — `_supervisor_pid(project) → pid`, None일 때 `(False, None)`, `_pid_is_alive(pid)` True면 `(True, pid)`, 아니면 `(False, None)`. public `tuple[bool, int | None]` 계약 불변 확인.
  - 세 함수 모두 handoff가 지정한 정확한 indentation/signature로 구성됐고, `IS_WINDOWS`, `_run`, `_wsl_path_str`, `FILE_QUERY_TIMEOUT`, `os.kill` 의존성은 그대로 사용.
- `pipeline_gui/backend.py:527-542`(`read_runtime_status`), `:602-606`(`runtime_state`) 미편집 확인. thin-reader shipped contract 그대로, `_supervisor_pid`/`_pid_is_alive` wiring 없음. 이는 handoff가 scope 밖으로 지정한 영역.
- `tests/test_pipeline_gui_backend.py:1135`의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator 단 한 줄만 삭제됨. 바로 이어지는 메서드 body(`:1136-1201`) 미변경. 주변 `:1133-1134`(이전 메서드 마지막 줄)과 `:1136`(unskipped 메서드 def) 정합 확인.
- 나머지 10개 skip decorator는 위치가 한 줄씩 밀렸지만(이전 `:594, :644, :719, :794, :869, :947, :1018, :1067, :1135, :1203, :1265` → 이제 `:594, :644, :719, :794, :869, :947, :1018, :1067, :1202, :1264`) 모두 동일 reason literal `"pipeline_gui_backend_state_transition_deferred"` 유지. 한 줄 삭제 + 1135 이후 구간 shift 영향만 있고 내용 변경 없음. 10개 카운트 정합.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465 shipped 표면 전부 미편집. `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, client/serializer/Playwright, `status_label` 4-literal set 모두 그대로. `git diff --check` 0건.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `468` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 469.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `466` — seq 467 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `467` — seq 468 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — seq 465 claude_handoff 이후 지속적으로 newest-valid-control(>462)에 의해 superseded 상태.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.054s`, `OK (skipped=10)`. baseline `OK (skipped=11)` → post-edit `OK (skipped=10)`. 새 failures/errors 없음. handoff 기대치 정합.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 1 test in 0.005s`, `OK`. unskipped 테스트의 raw-JSON pass-through assertion이 shipped thin-reader에서 clean pass.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests`(seq 453 baseline 유지 확인, 별도 verify 재실행).
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests`(seq 453 baseline 유지 확인).
- `-k claims`, `-k reinvestigation`는 `/work`가 각 7/6 OK로 기록했고, 이번 slice가 `tests/test_smoke.py`를 건드리지 않아 baseline 유지가 안전하게 추정됨. verify 라운드에서는 `-k progress_summary/coverage` 두 건을 재확인으로 충분히 다룸.
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과.
- `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드가 `pipeline_gui` + tests-only slice라 의도적으로 생략.

## 남은 리스크
- **10 cells 여전히 deferred**: `TestRuntimeStatusRead`의 나머지 10개 cell은 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")`로 남아 있고, 각각 `STOPPING→STOPPED`, `RUNNING→BROKEN`, `RUNNING→DEGRADED`, `degraded_reason` vocabulary 같은 sub-family를 인코딩합니다. 후속 G5-unskip-B/C/... 라운드가 각 sub-family를 bounded slice로 분할해 풀 수 있습니다.
- **helpers exist but unused by `read_runtime_status`**: `_supervisor_pid`/`_pid_is_alive`가 module-level mockable attribute로 존재하지만, 실제 thin-reader `read_runtime_status`는 이들을 호출하지 않습니다. 추가 cell unskip은 wiring을 함께 구현한 뒤 state-transition 검증을 같이 해야 무결성을 유지할 수 있습니다.
- **Gemini arbitration 패턴**: seq 461, seq 464의 non-bounded G5 advice 이후 seq 467이 bounded한 advice를 내놨고 이번 라운드가 truthful하게 closed. 패턴이 재발하면 다음 verify/handoff owner는 초기에 narrow 메뉴를 강조하거나 F-PIVOT 경로를 더 강하게 제시하는 편이 좋습니다. 현재는 loop이 풀려 진전이 있는 상태.
- **다음 슬라이스 ambiguity**: G3 / G5-unskip-B/C/... / G6-sub2(LocalOnlyHTTPServer bind) / G6-sub3(legacy `"단일 출처 상태"` fixture judgment) / G7(vocabulary enforcement) / G8(memory foundation) / G9(naming-collision cleanup) / G10(role_confidence COMMUNITY) / G11(SQLiteSessionStore adoption-list meta-audit)가 모두 서로 다른 축이고 dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 469)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests 잔존**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로, G6-sub2 후보 유지.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. pipeline_gui + tests slice이고 docs drift 유발 없음. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 해당 파일들을 건드리지 않음.
