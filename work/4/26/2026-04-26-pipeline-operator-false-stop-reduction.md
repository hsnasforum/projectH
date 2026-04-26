# 2026-04-26 pipeline operator false-stop reduction

## 변경 파일
- `.pipeline/README.md`
- `README.md`
- `pipeline_runtime/operator_autonomy.py`
- `watcher_prompt_assembly.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/4/26/2026-04-26-pipeline-operator-false-stop-reduction.md`

## 사용 skill
- `security-gate`: operator stop/approval 경계가 real-risk stop을 숨기지 않는지 확인했습니다.
- `doc-sync`: README와 `.pipeline/README.md`를 새 runtime 분류 truth에 맞췄습니다.
- `work-log-closeout`: 실제 변경 파일, 검증, 남은 리스크를 이 closeout에 정리했습니다.
- `finalize-lite`: 구현 종료 전 검증 사실, 문서 동기화, closeout 준비 상태를 좁게 확인했습니다.

## 변경 이유
- 오래 남은 release-gate operator stop header가 `OPERATOR_POLICY` / `REASON_CODE` 조합 때문에 structured fallback으로 떨어지면, agent가 처리할 수 있는 commit/push/doc-sync follow-up이 불필요하게 `needs_operator`로 보일 수 있었습니다.
- live `.pipeline/operator_request.md` CONTROL_SEQ 248의 `b1_release_gate_commit_authorization_dirty_tree` / `commit_publish_authorization` 조합도 같은 false-stop family로 확인됐습니다.
- 목표는 missing/unknown metadata는 계속 fail-safe operator stop으로 두면서, known legacy publish follow-up은 verify/handoff-owner follow-up으로 낮추는 것이었습니다.

## 핵심 변경
- `mNN_commit_push_milestones_doc_sync` 같은 legacy milestone commit/push/doc-sync reason을 `commit_push_bundle_authorization`으로 정규화했습니다.
- `bN_release_gate_commit_authorization_dirty_tree` reason과 `commit_publish_authorization` decision class를 canonical `commit_push_bundle_authorization + release_gate`로 정규화했습니다.
- `pr_creation_gate + commit_push_bundle_authorization`, `pr_creation_gate + gate_24h + release_gate`, `publication` 같은 compound/legacy header를 canonical operator policy와 decision class로 낮췄습니다.
- 모호한 generic `mNN_pr_gate`는 자동 매핑하지 않고, unknown publish metadata는 기존처럼 fail-safe `needs_operator`로 남게 했습니다.
- watcher prompt의 operator retriage 지시를 canonical release-gate metadata 우선으로 좁혔고, implement lane에 commit/push/PR 작업을 넘기지 않는 규칙은 유지했습니다.
- watcher/supervisor/operator schema 테스트에 legacy release-gate false-stop reduction과 unknown metadata fail-closed 회귀를 추가했습니다.
- README와 `.pipeline/README.md`에 legacy compound header 정규화와 real-risk 예외를 현재 구현 truth로 기록했습니다.

## 검증
- `python3 -m unittest -v tests.test_operator_request_schema`
  - 통과.
  - `Ran 29 tests in 0.004s`
- `python3 - <<'PY' ... classify_operator_candidate(.pipeline/operator_request.md) ... PY`
  - 통과.
  - live CONTROL_SEQ 248이 `triage commit_push_bundle_authorization internal_only release_gate operator_policy verify_followup False`로 분류됨을 확인했습니다.
- `python3 -m unittest -v tests.test_watcher_core`
  - 통과.
  - `Ran 204 tests in 9.563s`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_automation_health`
  - 통과.
  - `Ran 170 tests in 1.371s`
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py`
  - 통과, 출력 없음.
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py README.md .pipeline/README.md`
  - 통과, 출력 없음.

## 남은 리스크
- live supervisor/watcher 세션과 runtime soak는 실행하지 않았습니다. 이번 변경은 shared evaluator 정규화와 단위 회귀에 한정했습니다.
- real-risk stop(`truth_sync_required`, safety/destructive/auth/credential/approval-record repair, unresolved merge/publication boundary)은 기존 operator-visible 경계를 유지하도록 테스트했습니다.
- 작업 전 또는 병행 작업으로 보이는 `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, `work/4/25/2026-04-25-m31-bundle-publish-closeout.md`, `work/4/26/2026-04-26-m41-milestones-doc-sync.md`, `work/4/26/2026-04-26-m42-deep-doc-bundle.md`, `verify/4/26/2026-04-26-m41-axis2-milestones-doc-sync.md` 변경/미추적 항목은 이번 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, merge, 다음 slice 선택은 수행하지 않았습니다.
