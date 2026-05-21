# 2026-05-21 runtime policy publication default hold

## 변경 파일
- `.pipeline/config/runtime_policy.json` 신규 작성
- `pipeline_runtime/automation_health.py` 수정
- `pipeline_runtime/operator_autonomy.py` 수정
- `pipeline_runtime/supervisor.py` 수정
- `tests/test_pipeline_runtime_supervisor.py` 수정
- `work/5/21/2026-05-21-runtime-policy-publication-default-hold.md` 신규 작성

## 사용 skill
- `security-gate`: publication/operator 경계 완화 여부를 점검하고, push/PR/merge/auth 경계가 유지되는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 검증 결과, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `dirty_bundle_publication_or_hold_decision` 및 `publish_boundary_accumulated_dirty_tree` 계열 operator call이 반복적으로 발생하고, 운영 판단이 항상 publication hold로 수렴하는 상황을 standing runtime policy로 흡수하기 위해 변경했습니다.
- `commit/push/PR/merge/auth` 같은 실제 operator 경계는 그대로 유지하면서, publication-or-hold 질문만 기본 hold로 해소하도록 범위를 제한했습니다.

## 핵심 변경
- `.pipeline/config/runtime_policy.json`에 `publication_default: hold`, local commit 허용, remote push/PR create/PR merge는 `needs_operator`로 명시했습니다.
- `load_runtime_policy(project_root)`를 추가해 정책 파일이 없거나 JSON이 깨진 경우 `{}`로 fallback 하도록 했습니다.
- `resolve_operator_control()`에 `runtime_policy` 인자를 추가하고, policy가 hold일 때 `publication_boundary`, `pr_boundary`, `external_publication_boundary` 및 기존 publish-or-hold alias를 `publication_default_hold` stale marker로 낮추도록 했습니다.
- `pr_merge_gate`는 policy hold 대상에서 제외해 기존 gate marker와 verify follow-up backlog 동작을 유지했습니다.
- supervisor의 stale/gate operator control 해석 경로가 runtime policy를 전달하도록 했습니다.
- `publication_default_hold`를 automation health의 verify follow-up reason으로 등록해 status surface가 `verify_followup`을 유지하도록 했습니다.
- supervisor 회귀 테스트에 policy hold, dirty bundle alias hold, status-level verify follow-up 라우팅, `pr_merge_gate` 유지, policy 파일 없음 기존 동작 케이스를 고정했습니다.

## 검증
- 통과: `python3 -m json.tool .pipeline/config/runtime_policy.json >/tmp/runtime_policy.json.check`
- 통과: `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py`
- 최초 1회 실패 후 수정: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_publication_boundary_policy_hold_marks_operator_request_stale tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_dirty_bundle_publication_or_hold_policy_hold_marks_operator_request_stale tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pr_merge_gate_policy_hold_keeps_operator_gate_marker tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_dirty_bundle_publication_or_hold_operator_gate_routes_to_triage tests.test_pipeline_runtime_gate`
  - 실패 원인: 테스트가 `control_file`을 `operator_request.md`로 기대했지만 실제 supervisor snapshot은 `.pipeline/operator_request.md`를 반환했습니다.
  - 수정 후 결과: 통과, `Ran 42 tests`, `OK`.
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_publication_boundary_policy_hold_marks_operator_request_stale tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_dirty_bundle_publication_or_hold_policy_hold_marks_operator_request_stale tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_publication_default_hold_policy_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pr_merge_gate_policy_hold_keeps_operator_gate_marker tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_dirty_bundle_publication_or_hold_operator_gate_routes_to_triage tests.test_pipeline_runtime_gate`
  - 결과: `Ran 43 tests`, `OK`.
- 통과: `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_gate -v 2>&1 | tail -5`
  - 명령 exit code 0.
- 통과: `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py .pipeline/config/runtime_policy.json`
- 통과: `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py work/5/21/2026-05-21-runtime-policy-publication-default-hold.md`

## 남은 리스크
- 이번 변경은 runtime policy schema를 확장하거나 version migration을 만들지 않았습니다.
- watcher 쪽 직접 `resolve_operator_control()` 호출에는 runtime policy 전달을 추가하지 않았습니다. 이번 슬라이스는 handoff 범위대로 supervisor 경로에서 operator call surface를 줄이는 데 한정했습니다.
- `.pipeline/config/agent_profile.json`, `.claude/rules/pipeline-runtime.md`, 기존 `work/5/21/` 및 `verify/5/21/` dirty 항목은 이번 구현 전부터 존재한 변경이며, 이번 closeout에서는 되돌리거나 덮지 않았습니다.
- commit, push, PR 생성, merge, release, publication은 실행하지 않았습니다.
