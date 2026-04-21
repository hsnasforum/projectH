# 2026-04-21 operator retriage no-control recovery

## 변경 파일
- `watcher_core.py`
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.claude/rules/pipeline-runtime.md`
- `work/README.md`
- `verify/README.md`
- `work/4/21/2026-04-21-operator-retriage-no-control-recovery.md`

## 사용 skill
- `security-gate`: watcher가 canonical `.pipeline/gemini_request.md`를 machine-write하고 runtime control dispatch/drop 경계를 바꾸므로 위험 경계를 확인했습니다.
- `doc-sync`: runtime/control 동작 변경을 `.pipeline`, AGENTS/CLAUDE/GEMINI/PROJECT, work/verify README에 동기화했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 closeout으로 남겼습니다.

## 변경 이유
- 선택지형 operator stop이 verify/handoff retriage로 내려간 뒤, verify lane이 새 control 없이 idle로 돌아오면 같은 stop에 다시 묶여 진행이 멈출 수 있었습니다.
- 현재 실행 로그에서도 `gemini_advice_followup`이 lane busy로 deferred 된 뒤 `signal_mismatch`로 drop되어 follow-up prompt가 유실되는 정지 패턴이 확인됐습니다.
- 반복 멈춤을 줄이기 위해 no-next-control retriage는 advisory-first로 승격하고, follow-up/retriage pending prompt는 active control drift가 없는 한 큐에 보존하도록 경계를 좁혔습니다.

## 핵심 변경
- `watcher_core.py`에 `operator_retriage_no_next_control` 감지를 추가했습니다. gated operator request가 이미 verify/handoff retriage로 보내졌고 verify lane이 다시 prompt-ready idle인데 더 높은 control slot이 없으면, watcher가 다음 `CONTROL_SEQ`의 `.pipeline/gemini_request.md`를 atomic write하고 advisory turn으로 전환합니다.
- 새 advisory request는 원 `operator_request.md`, 최신 `/work`, 최신 `/verify`, advisory owner root doc을 `READ_FIRST`로 지정하고, `RECOMMEND: implement`, `RECOMMEND: close family and switch axis`, `RECOMMEND: needs_operator` 중 하나를 요구합니다.
- `watcher_dispatch.py`의 `signal_mismatch` pending drop을 `claude_handoff` dispatch에만 적용하도록 좁혔습니다. `gemini_advice_followup`, `codex_operator_retriage`, `codex_control_recovery`, `codex_blocked_triage`, `gemini_request`는 아직 paste되지 않은 deferred prompt일 수 있으므로 active control drift가 없으면 큐에 남습니다.
- `tests/test_watcher_core.py`에 operator retriage no-control이 `.pipeline/gemini_request.md`로 승격되는 replay와, supervisor `lane_working` + wrapper heartbeat 상황에서도 verify follow-up pending이 drop되지 않는 replay를 추가했습니다.
- 런타임을 `python3 -m pipeline_runtime.cli restart . --no-attach`로 재시작해 새 watcher가 적용됐고, 기존 `.pipeline/gemini_advice.md` seq 627 follow-up이 Claude verify lane으로 다시 전달되는 것을 확인했습니다.

## 검증
- `python3 -m py_compile watcher_core.py`
- `python3 -m unittest tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_promotes_to_gemini_request` (`Ran 1 test`, OK)
- `python3 -m unittest tests.test_watcher_core` (`Ran 157 tests`, OK)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` (`Ran 113 tests`, OK)
- `python3 -m py_compile watcher_core.py watcher_dispatch.py`
- `python3 -m unittest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_signal_mismatch_does_not_drop_verify_followup_pending tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_promotes_to_gemini_request` (`Ran 3 tests`, OK)
- `python3 -m unittest tests.test_watcher_core` (`Ran 158 tests`, OK)
- `git diff --check -- watcher_core.py watcher_dispatch.py tests/test_watcher_core.py .pipeline/README.md AGENTS.md CLAUDE.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md work/README.md verify/README.md` (출력 없음, OK)
- `python3 -m pipeline_runtime.cli restart . --no-attach` (rc=0)
- 재시작 후 `.pipeline/runs/20260421T070544Z-p202761/status.json`: `runtime_state=RUNNING`, active control `.pipeline/gemini_advice.md` seq 627, Claude lane `WORKING`, note `followup`.
- 상태 확인 중 `python3 scripts/pipeline_runtime_status.py --base-dir .pipeline`는 해당 스크립트가 없어 실패했고, 이후 `.pipeline/current_run.json`과 current run `status.json`을 직접 확인했습니다.

## 남은 리스크
- 이번 변경은 no-next-control operator retriage와 deferred follow-up prompt 유실을 막는 좁은 runtime recovery입니다. Gemini advice 내용을 watcher가 직접 해석해 handoff를 작성하지는 않습니다.
- 현재 seq 627 follow-up은 새 watcher에서 Claude lane으로 전달되어 진행 중입니다. Claude가 최종 control을 쓰면 그 다음 라운드는 별도 `/work` 또는 `/verify` truth에 맞춰 이어가야 합니다.
- live G4 `DISPATCH_SEEN` + `claude_handoff_idle_release` end-to-end 검증은 이번 코드 회귀와 restart 확인까지로 제한했고, 별도 operator/runtime validation 항목으로 남아 있습니다.
