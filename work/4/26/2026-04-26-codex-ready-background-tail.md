# 2026-04-26 codex ready background tail

## 변경 파일
- `pipeline_runtime/lane_surface.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/26/2026-04-26-codex-ready-background-tail.md`

## 사용 skill
- `security-gate`: runtime lane 상태, pane tail, task event surface가 자동화 진행 판단에 영향을 주므로 thin-client 재해석 없이 shared helper 경계에서 좁게 수정했다.
- `doc-sync`: 구현과 회귀 테스트에 맞게 runtime 운영 문서의 active busy marker 설명을 동기화했다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- controller server는 Codex lane을 `WORKING`으로 표시했지만 실제 terminal tail은 작업 완료 뒤 입력 prompt가 보이는 상태였다.
- 원인은 과거 완료 로그 `Waited for background terminal` 안의 `background terminal` 문자열이 active busy marker로 남아, `dispatch_seen`만 있는 active implement lane을 stale `WORKING`으로 부풀리는 경로였다.
- 같은 계열의 생산성 차단을 줄이기 위해 현재 진행형 busy와 과거 완료 로그를 구분하고, `dispatch_seen`만 남은 ready tail은 `prompt_visible`로 정리한다.

## 핵심 변경
- `pipeline_runtime/lane_surface.py`에서 active busy marker의 bare `background terminal`을 제거하고, 현재 진행형 `waiting for background`만 active wait로 유지했다.
- `pipeline_runtime/supervisor.py`에서 active lane이라도 tail이 `READY`이고 note가 `dispatch_seen...`이면 `prompt_visible`로 정규화하게 했다.
- watcher shared prompt test에 `Waited for background terminal` 뒤 Codex prompt가 busy를 막지 않는 회귀 케이스를 추가했다.
- supervisor lane status test에 active implement + `dispatch_seen seq 299` + completed background wait tail이 `READY/prompt_visible`로 내려오는 케이스를 추가했다.
- `.pipeline/README.md`와 runtime 설계/운영 문서에서 `Waiting for background terminal`은 busy, `Waited for background terminal` 뒤 prompt는 ready라는 현재 계약을 명시했다.

## 검증
- `python3 -m py_compile pipeline_runtime/lane_surface.py pipeline_runtime/supervisor.py watcher_core.py` 통과.
- `python3 -m unittest -v tests.test_watcher_core.PanePromptDetectionTest tests.test_pipeline_runtime_cli.WrapperEmitterTest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_active_dispatch_seen_codex_ready_tail_after_completed_background_wait_stays_ready tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_lane_background_terminal_wait_surfaces_working tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_ready_tail_clears_stale_dispatch_seen_note_for_inactive_ready_lanes` 통과: 23 tests.
- `git diff --check -- pipeline_runtime/lane_surface.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` 통과.
- `python3 -m pipeline_runtime.cli doctor . --session aip-projectH` 통과: fail=0, warn=0, ok=15.
- `python3 -m pipeline_runtime.cli status . --json` 확인: `runtime_state=RUNNING`, Codex lane `READY`, note `prompt_visible`.
- 문서 문구 확인용 `rg`는 처음 백틱 quoting 오류로 실패했고, single-quote 패턴으로 재실행해 `Waiting`/`Waited` 문구를 확인했다.

## 남은 리스크
- 전체 `tests.test_pipeline_runtime_supervisor`나 long soak는 실행하지 않았다. 변경 범위가 shared lane-surface marker와 supervisor ready-tail 보정에 한정되어 targeted unit과 live status 확인으로 좁게 검증했다.
- current active control `.pipeline/implement_handoff.md` seq 299는 여전히 docs-only implement handoff로 남아 있다. 이번 변경은 controller READY/WORKING 오표시를 줄이는 runtime fix이며, 해당 handoff의 문서 closure 자체를 완료하지는 않는다.
- 같은 파일들에는 앞선 runtime/operator-gate 작업에서 생긴 변경도 함께 남아 있다. 이번 closeout은 `Waited for background terminal` stale busy 판정과 `dispatch_seen` ready-tail 정규화 범위만 기록한다.
