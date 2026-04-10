# docs: reviewed-memory precondition family current-shipped apply/effect wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-precondition-family-shipped-apply-effect-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 claimed direct wording sync를 실제로 닫았는지 다시 확인할 필요가 있었습니다.
- 같은 reviewed-memory precondition family 안에서 남아 있는 residual drift를 기준으로 다음 Claude 슬라이스를 한 개로 다시 고정할 필요가 있었습니다.

## 핵심 변경
- 최신 `/work`는 부분적으로만 truthful했습니다. [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1473), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1483), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1490), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1492), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1493), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L858), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L865), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L871), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L648), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L654)의 직접 수정 자체는 현재 shipped apply/effect wording과 맞습니다.
- 다만 closeout의 `남은 리스크 없음` 판단은 과합니다. 같은 root authority docs family의 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1136), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1144), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1150), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L868), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L875), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L877), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L657), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L659)은 아직 rollback / disable / conflict meaning을 `later applied effect`, `future apply`, `future reviewed-memory layer`처럼 적고 있습니다.
- 실제 shipped truth는 [app/handlers/aggregate.py](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L392), [app/handlers/aggregate.py](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L467), [app/handlers/aggregate.py](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L529), [app/handlers/aggregate.py](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L636), [app/web.py](/home/xpdlqj/code/projectH/app/web.py#L302), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L7288), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L7300) 기준으로 apply result, stop-apply, reversal, conflict visibility까지 이미 열려 있습니다.
- 다음 Claude 슬라이스는 [.pipeline/claude_handoff.md](/home/xpdlqj/code/projectH/.pipeline/claude_handoff.md) 에 `Docs PRODUCT_SPEC ARCHITECTURE ACCEPTANCE_CRITERIA precondition meaning rollback-disable-conflict current-shipped wording truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-precondition-family-shipped-apply-effect-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-next-steps-emitted-record-layer-intro-shipped-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1470,1496p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '858,878p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '645,660p'`
- `rg -n "later applied influence|later applied effect|future reviewed-memory layer|when implemented|future apply|before any later apply" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1488,1493p'`
- `rg -n "disable handle|disable_handle|disable-side handle|disable_source_ref|reviewed_memory_disable_contract|reversible_effect_handle|applied_effect_target" app/serializers.py tests/test_web_app.py tests/test_smoke.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1128,1152p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1045,1118p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '995,1068p'`
- `rg -n "aggregate-transition-apply|future_reviewed_memory_stop_apply|future_reviewed_memory_reversal|future_reviewed_memory_conflict_visibility|effect_stopped|effect_reversed|conflict_visibility_checked" app/handlers/aggregate.py app/web.py tests/test_web_app.py tests/test_smoke.py`
- `git diff --check`
- Python unit test와 Playwright는 이번 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- reviewed-memory precondition family의 earlier meaning block이 root authority docs에서 아직 current shipped rollback / disable / conflict semantics를 완전히 닫지 못하고 있습니다.
