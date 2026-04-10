# docs: NEXT_STEPS TASK_BACKLOG aggregate item contract-object current-shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-planning-aggregate-contract-object-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 주장한 planning-doc aggregate item contract-object current-shipped wording sync가 실제 문서 상태와 맞는지 재검증할 필요가 있었습니다.
- 같은 recurrence aggregate family 안에서 다음 한 슬라이스를 operator 개입 없이 다시 고정할 필요가 있었습니다.

## 핵심 변경
- 최신 `/work`는 truthful하다고 확인했습니다. [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L122), [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L146), [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L156), [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L166), [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L177), [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L189), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L145), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L146), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L336), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L367), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L397), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L425), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L456) 의 contract-object heading은 현재 shipped wording과 맞습니다.
- 위 변경은 이미 current-shipped phrasing을 쓰고 있던 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L200), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L204), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L216), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L228), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L242), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L259) 과도 정합합니다.
- 다음 한 슬라이스는 `Docs ACCEPTANCE_CRITERIA operator-visible trigger-source layer shipped wording truth sync`로 고정했습니다. [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L744) 는 아직 trigger-source layer를 `later` slice처럼 적지만, [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1518), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L971), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L931), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L937) 는 이미 shipped/current wording으로 잠그고 있습니다.
- top-level `recurrence_aggregate_candidates` projection wording은 이번 다음 슬라이스로 선택하지 않았습니다. [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L239) 와 [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L196) 기준으로 해당 field는 aggregate가 없을 때 omission semantics를 가지므로, [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L101) 와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L144) 의 optional wording 자체는 현재 truthful합니다.

## 검증
- `rg -n "recurrence_aggregate_candidates|aggregate item now also exposes|now also expose" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md`
- `rg -n "recurrence_aggregate_candidates" app core storage tests docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "future_reviewed_memory_apply|remain later|rollback, disable, and operator-audit rules remain later|operator-visible.*future_reviewed_memory_apply" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- exact line spot-check via `nl -ba` on `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`, `app/serializers.py`, `tests/test_web_app.py`, `tests/test_smoke.py`, and the latest `/work`
- `git diff -- docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md .pipeline/claude_handoff.md`
- `git diff --check`
- Python unit test와 Playwright는 이번 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L744) 의 trigger-source layer가 아직 `later` wording을 남기고 있어, same-family authority-doc truth sync가 한 슬라이스 더 필요합니다.
