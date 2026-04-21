# 2026-04-21 advisory control health surface

## 변경 파일
- `watcher_prompt_assembly.py`
- `pipeline_runtime/automation_health.py`
- `watcher_core.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-advisory-control-health-surface.md`

## 사용 skill
- `security-gate`: watcher가 rolling control 파일과 lane dispatch를 자동으로 회수하는 경로를 추가하므로 승인/중단 경계와 파일쓰기 위험을 점검했습니다.
- `doc-sync`: automation health와 stale advisory 계약 변경을 `.pipeline/README.md`와 runtime 기술설계 문서에 맞췄습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 persistent `/work` 기록으로 남겼습니다.

## 변경 이유
- pipeline 런처 자동화에서 `ADVISORY_ACTIVE`가 열렸는데 `turn_state.active_control_file` / `active_control_seq`가 비어 있으면, 런처와 GUI가 현재 어떤 control을 기다리는지 덜 명확하게 보입니다.
- 오래 고착된 control이 advisory grace까지 지난 뒤에도 `automation_health=ok`로 남으면 no-silent-stall 계약과 맞지 않고, 사용자가 정상 진행과 멈춤을 구분하기 어렵습니다.

## 핵심 변경
- watcher startup이 `gemini_request.md`를 active advisory turn으로 잡을 때 `active_control_file=gemini_request.md`와 해당 `CONTROL_SEQ`를 `turn_state.json`에 함께 기록하도록 했습니다.
- `STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES` 이상 같은 control seq가 유지되면 `automation_health=attention`, `automation_reason_code=stale_control_advisory`, `automation_next_action=advisory_followup`으로 승격하도록 했습니다.
- `stale_control_advisory`를 advisory follow-up reason과 canonical incident family 문서에 추가했습니다.
- active `.pipeline/gemini_request.md`가 오래 열려 있고 같은 `CONTROL_SEQ`의 current `.pipeline/gemini_advice.md`가 없으면 watcher가 `gemini_advisory_recovery` event를 남기고 verify/handoff owner에게 recovery prompt를 보내도록 했습니다.
- recovery prompt는 advisory owner의 `.pipeline/gemini_advice.md`를 대필하지 않고, verify/handoff owner가 더 높은 `CONTROL_SEQ`의 implement handoff, 더 좁은 advisory request, 또는 실제 operator boundary 중 하나만 쓰도록 제한했습니다.
- 이미 `gemini_request.md`가 active control인 경우 stale-control advisory 작성기가 또 다른 Gemini request를 덮어쓰지 않도록 막아, advisory loop를 한 겹 더 쌓지 않게 했습니다.
- 런처/GUI thin-client 원칙은 유지했습니다. 새 추론을 launcher에 넣지 않고 supervisor/watcher가 쓰는 shared health 파생값과 turn state 기록만 보강했습니다.

## 검증
- `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py pipeline_runtime/automation_health.py` -> 통과
- `python3 -m unittest tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_control_age_after_advisory_grace_is_advisory_pending` -> 1 test OK
- `python3 -m unittest tests.test_watcher_core.WatcherPromptProfileTest.test_startup_advisory_turn_records_active_gemini_request_control` -> 실패, 테스트 클래스 이름 지정 착오(`WatcherPromptProfileTest` 없음)
- `python3 -m unittest tests.test_watcher_core.RuntimePlanConsumptionTest.test_startup_advisory_turn_records_active_gemini_request_control` -> 1 test OK
- `python3 -m unittest tests.test_watcher_core.ControlSeqAgeTrackerTest.test_stale_control_advisory_skips_when_gemini_request_active tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_gemini_advisory_recovers_to_verify_followup tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_gemini_advisory_recovery_skips_when_current_advice_exists` -> 3 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health` -> 19 tests OK
- `python3 -m unittest tests.test_watcher_core` -> 185 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_pipeline_launcher tests.test_pipeline_gui_home_presenter` -> 64 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` -> 129 tests OK
- `git diff --check` -> 통과
- `python3 -m pipeline_runtime.cli restart --mode experimental --session aip-projectH --no-attach .` -> 통과, 새 run `20260421T142742Z-p789418`
- runtime status 확인 -> `runtime_state=RUNNING`, `watcher.alive=true`, active control `.pipeline/gemini_advice.md` `CONTROL_SEQ: 724`, verify/handoff owner Claude가 follow-up 작업 중

## 남은 리스크
- 재시작 후 Claude verify/handoff owner가 `gemini_advice.md` `CONTROL_SEQ: 724`를 읽고 `NEXT_CONTROL_SEQ: 725` handoff를 작성 중입니다. 아직 `.pipeline/claude_handoff.md`는 seq 725로 갱신되지 않았습니다.
- `gemini_advisory_recovery`는 stale advisory를 1회 verify/handoff owner에게 회수시킵니다. 그 verify/handoff owner가 recovery/follow-up prompt를 받고도 새 control을 쓰지 못하는 경우의 별도 `verify_recovery_no_next_control`류 가드는 아직 없습니다.
- 이번 라운드는 synthetic soak를 돌리지 않았습니다. 재귀 개선 원칙에 맞춰 replay/unit 테스트와 runtime contract 문서 갱신까지만 수행했습니다.
- 이번 라운드에서는 commit/push/PR을 수행하지 않았습니다.
