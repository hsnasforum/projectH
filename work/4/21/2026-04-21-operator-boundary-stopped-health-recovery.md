# 2026-04-21 operator boundary stopped health recovery

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-operator-boundary-stopped-health-recovery.md`

## 사용 skill
- `security-gate`: approval/operator stop 경계와 runtime stop 표면을 바꾸는 작업이라 실제 위험 stop이 자동 진행으로 숨지 않는지 확인했습니다.
- `finalize-lite`: 구현 종료 전 검증 범위, docs sync, `/work` closeout 필요성을 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 기준으로 현재 노트를 남겼습니다.

## 변경 이유
- `approval_required + gate_24h` operator stop이 `pending_operator`/Gemini retriage로 밀리면서 Claude/Gemini가 같은 결정을 반복하는 루프가 있었습니다.
- live runtime이 `STOPPED`로 내려간 뒤 `automation_health=ok`, `automation_next_action=continue`로 남아 런처에서 정지 상태를 정상 진행처럼 볼 수 있었습니다.
- no-silent-stall 계약상 operator boundary와 stopped runtime은 원인/다음 행동을 명시해야 합니다.

## 핵심 변경
- `approval_required`, `safety_stop`, `truth_sync_required` 같은 real-risk reason은 `OPERATOR_POLICY: gate_24h`가 붙어도 `needs_operator` / `routed_to=operator`로 유지되게 했습니다.
- non-real-risk `slice_ambiguity` 계열만 `operator_retriage_no_next_control` / advisory follow-up으로 자동 라우팅되도록 watcher 테스트 기대를 정리했습니다.
- `runtime_state=STOPPED`이고 active incident/control이 없는 경우에도 `automation_health=attention`, `automation_reason_code=runtime_stopped`, `automation_next_action=operator_required`가 나오게 했습니다.
- `.pipeline/README.md`와 runtime 기술설계/운영 RUNBOOK에 real-risk gate와 stopped health 표면 계약을 동기화했습니다.
- live runtime을 새 코드로 재시작했고 현재는 `RUNNING + OPERATOR_WAIT`, active control `.pipeline/operator_request.md` seq 690, reason `approval_required`입니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py`
- `python3 -m unittest tests.test_watcher_core` → 162 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` → 124 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_pipeline_runtime_automation_health tests.test_pipeline_launcher tests.test_pipeline_gui_home_presenter` → 335 tests OK
- `git diff --check pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` → 통과
- `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py scripts/pipeline_runtime_gate.py` → 통과
- `python3 -m unittest tests.test_pipeline_runtime_automation_health` → 10 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` → 124 tests OK
- `python3 -m unittest tests.test_pipeline_gui_home_presenter tests.test_pipeline_launcher` → 40 tests OK
- `python3 -m unittest tests.test_watcher_core` → 162 tests OK
- `git diff --check pipeline_runtime/automation_health.py pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` → 통과
- live restart 확인: `.pipeline/runs/20260421T101505Z-p460279/status.json`에서 `runtime_state=RUNNING`, `watcher.alive=true`, `turn_state=OPERATOR_WAIT`, `automation_health=needs_operator`, `automation_reason_code=approval_required`를 확인했습니다.

## 남은 리스크
- 사용자가 실행한 6시간 `synthetic-soak`는 통과하지 못했습니다. 확인 시 부모 프로세스는 종료됐고, 임시 workspace `/tmp/projecth-pipeline-runtime-synthetic-rwnonmtf`의 runtime은 `STOPPED`였습니다. `report/pipeline_runtime/verification/`에는 이번 6시간 soak report가 새로 생기지 않았습니다.
- 수동 복구 시 `synthetic-soak`의 fake lane `extra_env` 없이 임시 workspace를 직접 `start`해 실제 Claude/Codex/Gemini trust prompt가 뜨는 부작용이 있었습니다. 이 수동 run도 종료됐고, 6시간 soak 증거로 쓰면 안 됩니다.
- 현재 live stop은 버그 루프가 아니라 `.pipeline/operator_request.md` seq 690의 실제 operator boundary입니다. 다음 진행은 dirty worktree commit/push 승인 또는 해당 operator_request를 대체하는 새 control 작성이 필요합니다.
