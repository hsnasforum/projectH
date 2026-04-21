# 2026-04-21 publication boundary health and merge follow-up

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `report/gemini/2026-04-21-automation-axis-complete-merge-and-milestone-gate.md`
- `work/4/21/2026-04-21-publication-boundary-health-and-merge.md`

## 사용 skill
- `security-gate`: PR merge와 publication boundary 표시는 외부 공개/승인 경계라서 자동 follow-up과 operator-required 경계를 분리했습니다.
- `doc-sync`: status/autonomy/health 계약 변경을 `.pipeline/README.md`와 runtime docs에 맞췄습니다.
- `work-log-closeout`: 실제 변경 파일, 검증, 남은 리스크를 persistent `/work` 기록으로 남겼습니다.
- `github`: PR #25 상태를 확인하고 merge 준비 경로를 확인했습니다.

## 변경 이유
- PR #25 draft 생성 이후 `.pipeline/operator_request.md` seq 722가 `external_publication_boundary`를 선언했지만, runtime status가 `autonomy.mode=hibernate`와 `automation_health=ok`를 함께 보여 operator wait를 정상 진행처럼 보이게 했습니다.
- `external_publication_boundary`는 draft PR 생성 follow-up이 아니라 merge/release/destructive publication 경계이므로, idle stable 또는 `gate_24h` metadata가 있어도 숨은 hibernate가 되면 안 됩니다.

## 핵심 변경
- `PUBLICATION_BOUNDARY_REASON_CODES`를 operator autonomy의 canonical reason set으로 추가했습니다.
- `external_publication_boundary` / `publication_boundary` / `pr_boundary`를 immediate operator-visible reason으로 분류해 `gate_24h + idle_stable`에서도 `needs_operator`로 남게 했습니다.
- automation health가 혹시 legacy `hibernate + external_publication_boundary` 상태를 읽더라도 `needs_operator + pr_boundary`로 보정하도록 했습니다.
- supervisor 재현 테스트를 추가해 operator_request seq 722 같은 케이스가 `automation_health=needs_operator`, `automation_next_action=pr_boundary`로 surface되는지 고정했습니다.
- Gemini advisory report를 tracked report로 포함해 seq 721/722 merge gate 근거를 persistent 기록으로 남겼습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py` -> 통과
- `python3 -m unittest tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_external_publication_boundary_stays_operator_visible tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_hibernating_publication_boundary_is_not_silent_ok tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_external_publication_boundary_operator_visible` -> 3 tests OK
- `python3 -m unittest tests.test_operator_request_schema` -> 14 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health` -> 19 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` -> 129 tests OK
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` -> 통과

## 남은 리스크
- 이 변경은 merge boundary를 정확히 `needs_operator + pr_boundary`로 보여주는 보정입니다. 사용자가 이번 라운드에서 PR #25 merge를 명시 승인했으므로, 이 closeout 이후 PR #25를 ready/merge하고 rolling operator gate는 더 높은 control로 supersede해야 합니다.
- GitHub milestone 객체는 repo에 현재 별도 milestone 항목이 없어 조작하지 않았습니다. "Milestone 5 전환"은 이번 라운드에서는 PR merge 후 다음 exact slice를 advisory/verify flow로 열어 운영 흐름을 전환하는 의미로 다룹니다.
