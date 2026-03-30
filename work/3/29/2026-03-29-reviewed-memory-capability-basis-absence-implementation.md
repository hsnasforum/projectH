# 2026-03-29 reviewed-memory capability-basis absence implementation

## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-capability-basis-absence-implementation.md`

## 사용 skill
- `mvp-scope`: current blocked capability layer와 later truthful basis layer를 다시 구분하고 구현 범위를 absence-preserving slice로 좁혔습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log` replay가 capability basis로 오해되지 않도록 점검했습니다.
- `doc-sync`: root docs와 `plandoc`를 current implementation truth에 맞춰 동기화했습니다.
- `release-check`: 실제 실행한 syntax, unittest, e2e, diff, `rg` 결과만 기준으로 라운드를 닫았습니다.
- `work-log-closeout`: 저장소 형식에 맞춰 이번 구현 라운드의 변경과 남은 리스크를 기록했습니다.

## 변경 이유
- 이전 closeout에서 first truthful `unblocked_all_required` capability-path contract는 문서로 닫혔지만, current repo에 exact later capability-basis source가 실제로 있는지는 아직 코드로 확인되지 않았습니다.
- current truth보다 더 ready하게 보이게 만들지 않으려면, fake `reviewed_memory_capability_basis`를 만들지 않고 aggregate serializer가 future basis layer를 어떻게 다루는지 코드와 회귀로 먼저 고정할 필요가 있었습니다.

## 핵심 변경
- `app/web.py`에 aggregate-level helper `_build_recurrence_aggregate_reviewed_memory_capability_basis(...)`를 추가했습니다.
- helper는 current transition-audit / unblock contract chain이 same exact aggregate와 계속 일치하는지까지는 확인하지만, current repo에 truthful later capability-basis source가 아직 없으므로 계속 `None`을 반환하도록 유지했습니다.
- `reviewed_memory_capability_status`는 matching basis object가 없으면 계속 `blocked_all_required`만 유지하도록 묶었습니다.
- fake `reviewed_memory_capability_basis` input이 들어와도 `reviewed_memory_capability_status`가 widen되지 않도록 막았습니다.
- focused regression을 추가해 ordinary aggregate payload에서 basis absence가 유지되는지, `candidate_review_record` / approval-backed save / historical adjunct / `task_log` replay 같은 support-only signals만으로 basis가 생기지 않는지, `reviewed_memory_transition_record` absence와 blocked trigger affordance semantics가 그대로인지 확인했습니다.
- root docs와 `plandoc`은 “aggregate serializer now probes the future basis layer, but current payload still emits no object because no truthful source exists”라는 현재 truth로 맞췄습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` tests passed
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_capability_status|reviewed_memory_transition_record|검토 메모 적용 시작|candidate_review_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크:
  - first truthful `unblocked_all_required` contract는 문서로 닫혔지만, current repo에 exact later capability-basis source가 실제로 있는지와 그 absence를 어떻게 보존할지는 아직 구현되지 않았습니다.
- 이번 라운드에서 해소한 리스크:
  - aggregate serializer가 future `reviewed_memory_capability_basis` layer를 평가하더라도, current repo truth에 맞게 object absence를 계속 보존하도록 고정했습니다.
  - fake basis input이나 support-only signals가 `reviewed_memory_capability_status`를 `unblocked_all_required`로 widen하는 경로를 줄였습니다.
- 여전히 남은 리스크:
  - truthful `reviewed_memory_capability_basis` source 자체는 아직 없습니다.
  - current aggregate card는 계속 blocked-only이며, enabled submit / note input / emitted transition record / reviewed-memory apply result는 여전히 later layer입니다.
  - repeated-signal promotion, cross-session counting, user-level memory는 계속 닫혀 있습니다.
