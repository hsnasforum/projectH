# 2026-03-30 aggregate-level reviewed-memory-apply-boundary verification

## 변경 파일
- `docs/NEXT_STEPS.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/TASK_BACKLOG.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `verify/3/30/2026-03-30-aggregate-level-reviewed-memory-apply-boundary-verification.md`

## 사용 skill
- `round-handoff`
- `doc-sync`

## 변경 이유
- 최신 `/work`인 `2026-03-30-aggregate-level-reviewed-memory-apply-boundary-only.md`는 aggregate-level reviewed-memory apply boundary가 구현되었다고 주장합니다.
- 최신 `/verify`인 `2026-03-30-aggregate-level-transition-record-emission-verification.md`는 emitted transition record까지만 검증했기 때문에 현재 기준으로 stale 여부를 다시 판정해야 했습니다.
- 현재 코드와 e2e는 apply boundary까지 가리키고 있었지만, 루트 문서 상단 요약 일부는 아직 emission-only 상태에 머물러 있어 current code truth와 partial stale mismatch가 있었습니다.

## 핵심 변경
- 필수 재검증을 다시 실행했고, 현재 환경에서 `py_compile`, focused unittest, `make e2e-test`, `git diff --check`가 모두 통과함을 확인했습니다.
- 현재 코드와 e2e를 다시 대조해 아래 shipped truth를 확인했습니다:
  - aggregate card는 emitted record 이후 `검토 메모 적용 실행` 버튼을 실제로 렌더링합니다.
  - 그 버튼은 실제 `/api/aggregate-transition-apply` POST로 이어집니다.
  - apply boundary 클릭 후 same `canonical_transition_id`를 유지한 채 `record_stage`가 `applied_pending_result`로 바뀌고 `applied_at`가 추가됩니다.
  - actual reviewed-memory apply result(메모리 효과 반영)는 여전히 absent입니다.
  - emitted transition record layer와 actual apply result는 여전히 separate입니다.
- 최신 `/verify`는 stale로 판정했습니다. 현재 truth는 `emitted transition record + no reviewed-memory apply`가 아니라 `emitted transition record + applied_pending_result boundary + no actual apply result`입니다.
- 루트 문서의 partial stale wording을 현재 shipped truth에 맞게 최소 범위로 sync했습니다:
  - `docs/NEXT_STEPS.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ARCHITECTURE.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
- 이번 라운드에서는 코드나 테스트를 바꾸지 않았고, actual reviewed-memory apply result, `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility`는 열지 않았습니다.
- 다음 최소 슬라이스는 `one truthful aggregate-level reviewed-memory apply result only`로 좁히는 것이 맞습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — `Ran 176 tests in 2.693s`, `OK`
- `make e2e-test` — `12 passed (4.0m)`
- `git diff --check` — 통과
- `rg -n "applied_pending_result|aggregate-transition-apply|검토 메모 적용 실행|reviewed_memory_transition_record|canonical_transition_id|applied_at|reviewed-memory apply result|next implementation step" app/web.py app/templates/index.html tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md` — code/e2e/docs truth 재대조에 사용

## 남은 리스크
- dirty worktree가 여전히 넓어서 다음 슬라이스도 unrelated 변경과 분리해서 좁게 진행해야 합니다.
- focused unittest는 helper 계약을 넓게 검증하지만 `apply_aggregate_transition` HTTP 경로 자체를 직접 고정하는 단위 테스트는 여전히 약하고, 현재 apply-boundary 경로의 end-to-end 보장은 Playwright smoke가 맡고 있습니다.
- `record_stage = applied_pending_result`는 apply boundary 도달만 뜻합니다. actual reviewed-memory apply result(메모리 효과 반영)는 아직 구현되지 않았습니다.
- `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility`는 여전히 닫혀 있습니다.
