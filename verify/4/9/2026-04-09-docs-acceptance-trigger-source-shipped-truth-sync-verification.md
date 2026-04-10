# docs: ACCEPTANCE_CRITERIA operator-visible trigger-source layer shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-acceptance-trigger-source-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 주장한 ACCEPTANCE trigger-source wording sync가 실제 문서 상태와 맞는지 재검증할 필요가 있었습니다.
- 같은 trigger-source / emitted-record family 안에서 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- 최신 `/work`는 truthful했습니다. [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L744) 는 이제 `the current shipped operator-visible trigger-source layer stays ...` 로 적혀 있고, 이는 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1518), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L971), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L931), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L937) 와 맞습니다.
- 다만 같은 family의 authority docs에는 residual wording이 남아 있습니다. [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1159), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1160), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1161) 는 아직 `future aggregate-level trigger-source layer`, `first later emitted transition surface`, `first later emitted record` 로 적지만, 같은 파일의 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L971) 부터 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L973), 그리고 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1529) 부터 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1533), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L762) 부터 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L763) 는 이미 current shipped layering으로 잠그고 있습니다.
- 다음 한 슬라이스는 `Docs ARCHITECTURE trigger-source and first emitted-record later wording truth sync`로 고정했습니다. 범위는 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1159) 부터 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1161) 까지의 residual `future/later` qualifier 정리입니다.

## 검증
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '739,749p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1516,1522p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '969,973p'`
- `rg -n "later operator-visible trigger-source|current shipped operator-visible trigger-source|trigger-source layer|Option A is shipped|future_reviewed_memory_apply" docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1148,1164p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1289,1299p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1526,1533p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '928,937p'`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md .pipeline/claude_handoff.md`
- `git diff --check`
- Python unit test와 Playwright는 이번 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1159) 부터 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1161) 까지의 `future/later` qualifier가 아직 current shipped trigger-source / emitted-record layering과 어긋나 있어, same-family truth sync가 한 슬라이스 더 필요합니다.
