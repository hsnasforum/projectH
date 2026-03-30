# 2026-03-30 reviewed-memory transition-audit-source-ref verification

## 변경 파일
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `verify/3/30/2026-03-30-reviewed-memory-transition-audit-source-ref-verification.md`

## 사용 skill
- `round-handoff`
- `doc-sync`

## 변경 이유
- 최신 `/work`인 `work/3/30/2026-03-30-reviewed-memory-transition-audit-source-ref-materialization-only.md`와 최신 `/verify`인 `verify/3/30/2026-03-30-reviewed-memory-round-handoff-truth-check.md`를 다시 대조해, stale 여부와 현재 shipped truth를 재판정해야 했습니다.
- 최신 `/verify`는 최신 `/work`를 정확히 가리키지 못했고, 문서 일부도 이전 `source family incomplete` 상태를 남기고 있어 그대로 후속 handoff truth로 쓰기 어려웠습니다.
- 이번 라운드의 목적은 구현 확장이 아니라 현재 코드/테스트/문서를 truthful state로 다시 맞추고, 실제 검증을 재실행한 뒤 `ready / not ready`를 판정하는 것이었습니다.

## 핵심 변경
- `app/web.py` 기준으로 `_resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(...)`가 실제로 존재하고, exact same-aggregate `reviewed_memory_transition_audit_contract`와 shared `reviewed_memory_applied_effect_target`가 모두 맞을 때만 internal `transition_audit_source_ref`를 materialize하는 것을 재확인했습니다.
- `app/web.py` 기준으로 internal `_build_recurrence_aggregate_reviewed_memory_capability_source_refs(...)` family가 이제 all five refs (`boundary_source_ref`, `rollback_source_ref`, `disable_source_ref`, `conflict_source_ref`, `transition_audit_source_ref`) complete이며 `source_status = all_required_sources_present`인 것을 재확인했습니다.
- 반대로 `reviewed_memory_capability_basis`는 여전히 absent이고, `reviewed_memory_capability_status.capability_outcome`는 여전히 `blocked_all_required`이며, aggregate card `검토 메모 적용 시작`은 계속 visible-but-disabled이고, `reviewed_memory_transition_record`는 계속 absent인 것을 재확인했습니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`도 같은 truth를 기대값으로 고정하고 있음을 다시 확인했습니다.
- 최신 `/verify`는 stale로 판정했습니다. 이유는 최신 `/work`보다 한 단계 뒤의 파일을 근거로 쓰고 있었고, 문서 일부의 이전 unresolved wording을 그대로 남겨 현재 code truth와 어긋났기 때문입니다.
- 이번 라운드에서 `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`의 stale wording만 최소 수정해, `transition_audit_source_ref resolved / source family complete / basis absent / blocked 유지` truth에 맞췄습니다.

## 검증
- `rg -n "transition_audit_source_ref|reviewed_memory_capability_source_refs|reviewed_memory_capability_basis|blocked_all_required|unblocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 176 tests in 2.678s`
  - `OK`
- `make e2e-test`
  - 1차 실패: `Error: http://127.0.0.1:8879 is already used`
  - 추가 확인:
    - `lsof -iTCP:8879 -sTCP:LISTEN -n -P`
    - `ps -ef | rg "app.web --host 127.0.0.1 --port 8879|playwright test|node .*8879|python3 -m app.web"`
    - `curl -I --max-time 5 http://127.0.0.1:8879`
    - `kill 136200 136199`
  - 2차 재실행: 실제 smoke 실행까지 진입했지만 최종 `12 failed`
  - 첫 실제 실패:
    - `tests/web-smoke.spec.mjs:103:1 › 파일 요약 후 근거와 요약 구간이 보입니다`
    - `response-box`에 expected summary text가 나타나지 않음
  - 후속 실패 패턴:
    - 나머지 11개는 `page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:8879/`
    - 첫 시나리오 뒤 mock webServer가 내려간 뒤 연쇄 실패한 패턴으로 보임
- `git diff --check`
  - 통과
- stale wording 재확인:
  - `rg -n 'remaining three refs unresolved|until that later source family exists|keeps the remaining three refs unresolved|full matching source family does not exist' docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과 없음

## 남은 리스크
- 현재 라운드는 `not ready`입니다. `make e2e-test`가 green이 아니고, 첫 browser smoke 이후 mock webServer가 내려가며 나머지 시나리오가 연쇄 `ERR_CONNECTION_REFUSED`로 실패했습니다.
- 최신 `/work`의 핵심 주장 자체는 현재 코드/테스트와 맞습니다:
  - `transition_audit_source_ref` resolved
  - internal `reviewed_memory_capability_source_refs` family complete
  - `reviewed_memory_capability_basis` absent
  - `reviewed_memory_capability_status.capability_outcome = blocked_all_required`
  - aggregate card `검토 메모 적용 시작` disabled
  - `reviewed_memory_transition_record` absent
- 이번 라운드에서 stale docs wording은 정리했지만, 브라우저 smoke red 상태 때문에 shipped readiness는 아직 확보되지 않았습니다.
- e2e 첫 실패의 근본 원인 서버 예외 스택까지는 이번 라운드에서 추적하지 않았습니다. 현재 확인된 사실은 첫 summary assertion 실패 뒤 webServer가 내려가고, 이후 11개가 접속 불가로 연쇄 실패했다는 것까지입니다.
- dirty worktree가 매우 넓습니다. 다음 라운드는 reviewed-memory basis를 열지 말고, browser smoke first-failure / server-exit repair 범위로만 좁혀야 합니다.
