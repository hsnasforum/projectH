# docs: precondition meaning rollback-disable-conflict current-shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-precondition-meaning-rollback-disable-conflict-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 precondition meaning block의 rollback/disable/conflict wording을 실제로 모두 닫았는지 다시 확인할 필요가 있었습니다.
- 같은 family 안에서 다음 Claude 슬라이스를 다시 한 개로 좁힐 필요가 있었습니다.

## 핵심 변경
- 최신 `/work`는 부분적으로만 truthful했습니다. [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L864), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L647), 그리고 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1136), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1144), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1148), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1150)의 직접 수정 다수는 현재 shipped framing과 맞습니다.
- 다만 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1139) 와 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L1140) 은 아직 `later applied effect`, `future influence`, `future reviewed-memory effect` 표현을 남기고 있어 같은 meaning block을 완전히 닫지 못합니다.
- 실제 shipped truth는 [app/handlers/aggregate.py](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L392), [app/handlers/aggregate.py](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L467), [app/handlers/aggregate.py](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L529), [app/handlers/aggregate.py](/home/xpdlqj/code/projectH/app/handlers/aggregate.py#L636), [app/web.py](/home/xpdlqj/code/projectH/app/web.py#L302), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L7288), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L7300) 기준으로 apply result, stop-apply, reversal, conflict visibility까지 이미 열려 있습니다.
- 다음 Claude 슬라이스는 [.pipeline/claude_handoff.md](/home/xpdlqj/code/projectH/.pipeline/claude_handoff.md) 에 `Docs PRODUCT_SPEC precondition rollback meaning current-shipped wording truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-precondition-meaning-rollback-disable-conflict-shipped-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-precondition-family-shipped-apply-effect-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1134,1152p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '864,878p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '647,660p'`
- `rg -n "later applied effect|later applied influence|future reviewed-memory layer|future influence stop|before any later apply|later disable handles when implemented|later disable handle when implemented|when implemented" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- Python unit test와 Playwright는 이번 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md`의 same-family rollback meaning 두 줄이 아직 current shipped wording을 완전히 닫지 못하고 있습니다.
