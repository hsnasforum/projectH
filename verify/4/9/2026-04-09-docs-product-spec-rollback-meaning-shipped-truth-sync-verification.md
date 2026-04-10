# docs: PRODUCT_SPEC precondition rollback meaning current-shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-spec-rollback-meaning-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 PRODUCT_SPEC rollback meaning residual을 실제로 닫았는지 다시 확인할 필요가 있었습니다.
- 같은 reviewed-memory precondition family에서 다음 Claude 슬라이스를 다시 한 개로 좁힐 필요가 있었습니다.

## 핵심 변경
- 최신 `/work`는 직접 수정 claim 자체는 truthful했습니다. [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1139) 와 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1140) 은 이제 `applied reviewed-memory effect`와 `that effect's influence` wording으로 바뀌어 shipped rollback semantics와 맞습니다.
- 다만 closeout의 `남은 리스크 없음` 판단은 과합니다. 같은 precondition meaning family의 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1129), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L860), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L643)은 아직 `future reviewed memory` / `later reviewed memory` boundary wording을 남기고 있습니다.
- 실제 current shipped truth는 [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L1138), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L1432), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L1480), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L1223), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L1304), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L1321) 기준으로 `reviewed_memory_boundary_draft`, `reviewed_memory_unblock_contract`, `reviewed_memory_capability_status`가 이미 current aggregate surface에 materialize되어 있다는 점입니다.
- 다음 Claude 슬라이스는 [.pipeline/claude_handoff.md](/home/xpdlqj/code/projectH/.pipeline/claude_handoff.md) 에 `Docs PRODUCT_SPEC ARCHITECTURE ACCEPTANCE_CRITERIA boundary_defined current-shipped wording truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-product-spec-rollback-meaning-shipped-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-precondition-meaning-rollback-disable-conflict-shipped-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1136,1142p'`
- `rg -n "later applied effect|future influence|future reviewed-memory effect|later disable handle when implemented|later disable handles when implemented|disable-side handle \\(when implemented\\)|when implemented" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "future reviewed memory must have|future reviewed-memory effect must|reviewed-memory layer must keep competing|same_session_exact_recurrence_aggregate_only" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1128,1134p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '858,864p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '642,647p'`
- `nl -ba app/serializers.py | sed -n '1138,1158p'`
- `nl -ba app/serializers.py | sed -n '1432,1498p'`
- `nl -ba tests/test_web_app.py | sed -n '1210,1328p'`
- `git diff --check`
- Python unit test와 Playwright는 이번 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- `reviewed_memory_boundary_defined` meaning line의 future/later boundary framing이 root authority docs 세 곳에 아직 남아 있습니다.
