# 2026-04-21 PR creation gate visible boundary

> 후속 변경: `work/4/21/2026-04-21-pr-creation-auto-followup-routing.md`에서 사용자의 명시 지시에 따라 `pr_creation_gate + gate_24h + release_gate`를 operator wait가 아니라 draft PR 생성 자동 follow-up으로 재정의했습니다. 아래 기록은 이 전 라운드의 당시 판단과 검증 사실입니다.

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-pr-creation-gate-visible-boundary.md`

## 사용 skill
- `security-gate`: PR 생성은 외부 publication boundary이므로 자동 실행이 아니라 명시 operator boundary로 남겨야 함을 확인했습니다.
- `doc-sync`: `pr_creation_gate` surface 계약을 `.pipeline/README.md`와 runtime 설계/운영 문서에 맞췄습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, live 확인 결과, 남은 리스크를 이 closeout에 기록했습니다.

## 변경 이유
- runtime 재시작 후 `.pipeline/operator_request.md`에는 `CONTROL_SEQ: 717`, `REASON_CODE: pr_creation_gate`, `OPERATOR_POLICY: gate_24h`, `DECISION_CLASS: release_gate`가 살아 있었지만 status는 `ok + IDLE`로 보였습니다.
- 원인은 `pr_creation_gate`가 canonical reason으로 등록되어 있지 않아 `gate_24h` suppress path에서 `hibernate`로 분류됐기 때문입니다.
- PR 생성/마일스톤 전환은 자동화가 조용히 넘길 일이 아니라 operator publication boundary이므로, 숨은 idle 대신 `needs_operator + pr_boundary`로 드러나야 합니다.

## 핵심 변경
- `PR_CREATION_GATE_REASON = "pr_creation_gate"`를 shared reason constant로 추가하고 immediate operator-visible reason에 등록했습니다.
- automation health의 `PR_BOUNDARY_REASONS`에 `pr_creation_gate`를 추가해 `automation_next_action=pr_boundary`로 표시되게 했습니다.
- operator schema, automation health, supervisor status 회귀 테스트를 추가해 `pr_creation_gate + gate_24h + release_gate`가 `needs_operator` current truth로 남는지 고정했습니다.
- `.pipeline/README.md`, runtime 기술설계, 운영 RUNBOOK에 PR gate는 hibernate가 아니라 visible publication boundary라고 명시했습니다.
- live runtime을 재시작해 `.pipeline/operator_request.md` seq 717이 `OPERATOR_WAIT`, `automation_health=needs_operator`, `automation_reason_code=pr_creation_gate`, `automation_next_action=pr_boundary`로 표시되는 것을 확인했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py` -> 통과
- `python3 -m unittest tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_pr_creation_gate_is_operator_visible_release_boundary tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_pr_creation_gate_maps_to_pr_boundary tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_pr_creation_gate_as_pr_boundary` -> 3 tests OK
- `python3 -m unittest tests.test_operator_request_schema` -> 13 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health` -> 18 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` -> 128 tests OK
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` -> 통과
- `python3 -m pipeline_runtime.cli restart --mode experimental --no-attach .` -> 종료 코드 0
- live status 확인: current run `20260421T132441Z-p712636`, `runtime_state=RUNNING`, `watcher_alive=true`, `active_control_file=.pipeline/operator_request.md`, `active_control_seq=717`, `turn_state=OPERATOR_WAIT`, `automation_next_action=pr_boundary`

## 남은 리스크
- 이 변경은 PR을 자동 생성하지 않습니다. PR 생성은 외부 publication boundary라 `pr_creation_gate`에서 operator 결정으로 남기는 것이 현재 안전 계약입니다.
- 현재 worktree에는 이 round 변경 외에도 이전 closeout 보정 파일과 `report/gemini/2026-04-21-automation-axis-closure-and-pr-transition.md` untracked 항목이 남아 있습니다. 이는 별도 정리/커밋 범위 판단이 필요합니다.
