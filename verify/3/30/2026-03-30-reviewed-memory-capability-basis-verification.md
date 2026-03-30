# 2026-03-30 reviewed-memory capability-basis verification

## 변경 파일
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `verify/3/30/2026-03-30-reviewed-memory-capability-basis-verification.md`

## 사용 skill
- `round-handoff`
- `doc-sync`

## 변경 이유
- 최신 `/work`인 `2026-03-30-reviewed-memory-capability-basis-materialization-only.md`는 `reviewed_memory_capability_basis`가 truthfully materialized 되었다고 주장합니다.
- 최신 `/verify`인 `2026-03-30-e2e-568-recurrence-aggregate-verification.md`는 그 직전 basis-absent 기준의 handoff를 담고 있어 stale 여부를 다시 판정해야 했습니다.
- 루트 문서 일부가 이미 basis present를 적으면서도 다음 슬라이스를 여전히 `reviewed_memory_capability_basis materialization only`로 남겨 현재 코드/테스트 truth와 충돌하고 있었습니다.

## 핵심 변경
- 필수 재검증을 다시 실행했고, 현재 환경에서 `py_compile`, focused unittest, `make e2e-test`, `git diff --check`가 모두 통과함을 확인했습니다.
- 현재 코드와 테스트를 다시 대조해 아래 shipped truth를 확인했습니다:
  - `reviewed_memory_capability_basis` present
  - `reviewed_memory_capability_status.capability_outcome = blocked_all_required`
  - aggregate card `검토 메모 적용 시작` stays `visible_disabled`
  - `reviewed_memory_transition_record` absent
- 최신 `/verify`는 stale로 판정했습니다. 현재 truth는 basis-absent가 아니라 basis-present이며, 다음 최소 슬라이스도 더 이상 basis materialization only가 아닙니다.
- 루트 문서의 stale wording만 최소 범위로 sync했습니다:
  - `docs/NEXT_STEPS.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ARCHITECTURE.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
- 이번 라운드에서는 코드나 테스트를 바꾸지 않았고, `unblocked_all_required`, enabled submit flow, emitted transition record는 열지 않았습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — `Ran 176 tests in 2.091s`, `OK`
- `make e2e-test` — `12 passed (3.8m)`
- `git diff --check` — 통과
- `rg -n "reviewed_memory_capability_basis|capability_outcome|unblocked_all_required|reviewed_memory_transition_record|next truthful|next slice|basis materialization" app/web.py tests/test_smoke.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md` — 코드/테스트 truth와 루트 문서 wording 재대조에 사용

## 남은 리스크
- dirty worktree가 여전히 넓어서 다음 슬라이스도 unrelated 변경과 분리해서 좁게 진행해야 합니다.
- `reviewed_memory_capability_basis` present는 `unblocked_all_required`를 뜻하지 않습니다.
- enabled submit flow, `reviewed_memory_transition_record`, reviewed-memory apply result는 여전히 닫혀 있습니다.
