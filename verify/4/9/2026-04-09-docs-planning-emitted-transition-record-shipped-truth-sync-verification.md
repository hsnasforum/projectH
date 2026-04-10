# docs: NEXT_STEPS TASK_BACKLOG emitted-transition-record current-shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-planning-emitted-transition-record-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 주장한 planning emitted-transition-record wording sync가 실제 문서 상태와 맞는지 재검증할 필요가 있었습니다.
- 같은 emitted-record / reviewed-memory-apply family 안에서 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정은 truthful했습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L653) 는 이제 `the current shipped emitted-transition-record materializes only for ...` 로 적고, [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L402) 와 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L403) 도 reviewed-memory apply / emitted transition record를 current shipped layering으로 맞췄습니다. 이는 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1529) 부터 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1533), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1160) 부터 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1164), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L928) 부터 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L937) 와 정합합니다.
- 다만 closeout의 `남은 리스크 없음` 판단은 과합니다. 같은 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L206) block이 아직 `exact same-session unblock semantics should now stay fixed before any emitted transition record or apply vocabulary opens` 로 남아 있는데, 이는 같은 family의 current shipped truth와 어긋납니다. 이미 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L271) 부터 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L278), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1524) 부터 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1530), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1160) 부터 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1164), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L920) 부터 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L930) 는 emitted record / apply path가 이미 readiness layer 위에 shipped라고 잠급니다.
- 다음 한 슬라이스는 `Docs NEXT_STEPS exact same-session unblock semantics shipped wording truth sync` 로 고정했습니다. 범위는 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L206) 의 stale `before ... opens` phrasing 정리입니다.

## 검증
- `nl -ba docs/TASK_BACKLOG.md | sed -n '650,655p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '399,404p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1528,1533p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1160,1164p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '928,937p'`
- `rg -n "may materialize only for|current shipped .* materializes only for|now shipped alongside|reviewed-memory apply, or cross-session counting|later emitted transition record|reviewed-memory apply vocabulary" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '202,214p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '222,236p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1515,1526p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1152,1164p'`
- `rg -n "before any emitted transition record or apply vocabulary opens|emitted transition record or apply vocabulary opens|exact same-session unblock semantics should now stay fixed before" docs/NEXT_STEPS.md docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `git diff --check`
- Python unit test와 Playwright는 이번 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L206) 의 `before any emitted transition record or apply vocabulary opens` phrasing이 아직 current shipped truth와 어긋나 있어, same-family truth sync가 한 슬라이스 더 필요합니다.
