## 변경 파일
- `verify/4/9/2026-04-09-docs-transition-apply-residual-absence-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/9/2026-04-09-docs-transition-apply-residual-absence-truth-sync.md`가 `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`의 reviewed-memory transition/apply 부재 문구를 shipped truth에 맞게 고쳤다고 기록했으므로, 실제 반영 여부와 closeout의 truthful 여부를 다시 확인할 필요가 있었습니다.
- 직전 `/verify`인 `verify/4/9/2026-04-09-docs-acceptance-review-action-regression-header-truth-sync-verification.md`가 같은 reviewed-memory docs family의 다음 한 슬라이스를 root authority docs residual absence sync로 고정했으므로, 이번 라운드에서는 그 handoff가 실제로 닫혔는지와 남은 same-family follow-up을 함께 정리해야 했습니다.

## 핵심 변경
- 최신 `/work`는 truthful했습니다. [docs/ARCHITECTURE.md:1132](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1132) 는 이제 `no reviewed-memory candidate store`만 유지하면서 apply path shipped truth를 직접 닫고, [docs/ARCHITECTURE.md:1168](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L1168) 은 emitted transition record surface shipped truth를 직접 닫습니다. [docs/PRODUCT_SPEC.md:1540](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1540) 도 `reviewed-memory apply result is now shipped`로 정리되어 [docs/PRODUCT_SPEC.md:1537](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1537) 의 상세 shipped section과 맞습니다.
- 위 수정은 실제 구현과도 맞습니다. [app/web.py:302](/home/xpdlqj/code/projectH/app/web.py#L302) 부터 [app/web.py:306](/home/xpdlqj/code/projectH/app/web.py#L306) 은 apply/result/stop/reverse/conflict-check endpoint를 노출하고, [app/handlers/aggregate.py:392](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L392) 부터 [app/handlers/aggregate.py:415](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L415) 는 `apply_result`와 `reviewed_memory_active_effects`를 materialize하며, [app/handlers/aggregate.py:467](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L467) 부터 [app/handlers/aggregate.py:532](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L532) 는 stopped/reversed state를 갱신합니다.
- 다만 같은 docs family의 다음 follow-up은 아직 남아 있습니다. [docs/ACCEPTANCE_CRITERIA.md:806](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L806) 는 아직 `the current contract still must not emit ... a reviewed-memory apply path`라고 적어 global absence처럼 읽히지만, 같은 문서의 [docs/ACCEPTANCE_CRITERIA.md:763](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L763) 부터 [docs/ACCEPTANCE_CRITERIA.md:776](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L776), [docs/ACCEPTANCE_CRITERIA.md:920](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L920) 부터 [docs/ACCEPTANCE_CRITERIA.md:967](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L967) 은 이미 emitted transition / apply / stop-apply / reversal을 current shipped로 설명합니다. authority docs도 [docs/PRODUCT_SPEC.md:1178](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1178) 부터 [docs/PRODUCT_SPEC.md:1203](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1203), [docs/ARCHITECTURE.md:907](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L907) 부터 [docs/ARCHITECTURE.md:913](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L913) 에서 planning-target / unblock meaning이 apply보다 좁다는 local guardrail로 적을 뿐, global 부재처럼 쓰지 않습니다.
- 다음 한 슬라이스는 [.pipeline/claude_handoff.md](/home/xpdlqj/code/projectH/.pipeline/claude_handoff.md) 에 `Docs ACCEPTANCE_CRITERIA recurrence-key guardrail reviewed-memory apply-path local wording truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-transition-apply-residual-absence-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-acceptance-review-action-regression-header-truth-sync-verification.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1528,1545p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1128,1172p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1184,1206p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '760,808p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '900,926p'`
- `rg -n "no reviewed-memory apply path|reviewed-memory apply path is now shipped|emitted reviewed-memory transition record surface is now shipped|reviewed-memory apply result is now shipped|no reviewed-memory candidate store" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n "marker remains read-only and blocked|no reviewed-memory apply path|planning-target source|reviewed_memory_planning_target_ref|target_boundary = reviewed_memory_draft_planning_only" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `nl -ba app/web.py | sed -n '296,346p'`
- `nl -ba app/handlers/aggregate.py | sed -n '388,420p;464,538p'`
- `git diff --check`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 `git diff --check`만 다시 확인했습니다.
- Python unit test와 Playwright는 재실행하지 않았습니다.
