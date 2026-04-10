# docs: ARCHITECTURE trigger-source and first emitted-record later wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-architecture-trigger-source-emitted-record-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 주장한 ARCHITECTURE trigger-source / emitted-record wording sync가 실제 문서 상태와 맞는지 재검증할 필요가 있었습니다.
- 같은 trigger-source / emitted-record family 안에서 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- 최신 `/work`는 truthful했습니다. [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1159), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1160), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1161) 는 이제 current shipped trigger-source / emitted-record layering과 맞고, 이는 같은 파일의 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L971) 부터 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L973), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1529) 부터 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1533), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L762) 부터 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L763) 와 정합합니다.
- 다만 같은 family의 planning docs에는 residual wording이 남아 있습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L653) 는 아직 `the first emitted-transition-record implementation may materialize only for ...` 로 적고, [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L402) 와 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L403) 는 emitted transition record / reviewed-memory apply를 아직 later reopening처럼 읽히게 만듭니다. 하지만 shipped truth는 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1529) 부터 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1533), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1160) 부터 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1164), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L928) 부터 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L937) 기준으로 이미 열려 있습니다.
- 다음 한 슬라이스는 `Docs NEXT_STEPS TASK_BACKLOG emitted-transition-record current-shipped wording truth sync`로 고정했습니다. 범위는 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L653) 과 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L402) 부터 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L403) 까지의 residual planning wording 정리입니다.

## 검증
- `nl -ba docs/ARCHITECTURE.md | sed -n '1154,1164p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '969,973p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1528,1533p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '762,763p'`
- `rg -n "future aggregate-level trigger-source layer|current shipped aggregate-level trigger-source layer|first later emitted transition surface|current shipped emitted transition surface|that emitted record materializes only for|first later emitted record|first emitted-transition-record slice is now implemented|trigger-source layer exists" docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `nl -ba docs/MILESTONES.md | sed -n '314,336p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '239,262p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '648,668p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1528,1534p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '762,764p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '388,406p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '652,657p'`
- `rg -n "may materialize only for|later emitted transition record|later emitted record|enabled submit and emitted-record materialization are now shipped|first truthful emission trigger" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff -- docs/ARCHITECTURE.md .pipeline/claude_handoff.md`
- `git diff --check`
- Python unit test와 Playwright는 이번 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L653) 와 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L402) 부터 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L403) 까지의 planning wording이 아직 current emitted-record / reviewed-memory apply truth와 어긋나 있어, same-family truth sync가 한 슬라이스 더 필요합니다.
