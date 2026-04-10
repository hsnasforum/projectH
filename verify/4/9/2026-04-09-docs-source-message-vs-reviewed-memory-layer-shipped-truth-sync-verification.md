# docs: source-message trace vs reviewed-memory layer current-shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-source-message-vs-reviewed-memory-layer-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` note의 source-message trace vs reviewed-memory layer summary 수정이 실제 current shipped contract와 맞는지 다시 확인해야 했습니다.
- 같은 reviewed-memory precondition family 안에서 다음 Claude 슬라이스를 한 개로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 6줄은 truthful했습니다.
  - `docs/PRODUCT_SPEC.md:1059`
  - `docs/PRODUCT_SPEC.md:1062`
  - `docs/ARCHITECTURE.md:798`
  - `docs/ARCHITECTURE.md:802`
  - `docs/ACCEPTANCE_CRITERIA.md:585`
  - `docs/ACCEPTANCE_CRITERIA.md:589`
  는 이제 source-message trace와 reviewed-memory layer summary를 current shipped surface 기준으로 설명합니다.
- 다만 closeout의 `남은 리스크 없음`은 과합니다.
  - `docs/PRODUCT_SPEC.md:1159`
  - `docs/ARCHITECTURE.md:889`
  - `docs/ACCEPTANCE_CRITERIA.md:666`
  는 아직 `operator_auditable_reviewed_memory_transition`을 `any later reviewed-memory transition`처럼 적고 있습니다.
- 실제 shipped truth는 이미 emitted/apply/stop/reversal/conflict-visibility까지 열려 있습니다.
  - `docs/PRODUCT_SPEC.md:1529`
  - `docs/PRODUCT_SPEC.md:1531`
  - `docs/PRODUCT_SPEC.md:1532`
  - `docs/ARCHITECTURE.md:971`
  - `docs/ACCEPTANCE_CRITERIA.md:928`
  - `docs/ACCEPTANCE_CRITERIA.md:937`
  - `app/handlers/aggregate.py:392`
  - `app/handlers/aggregate.py:467`
  - `app/handlers/aggregate.py:529`
  - `app/handlers/aggregate.py:554`
  - `tests/test_web_app.py:7488`
  - `tests/test_web_app.py:7643`
  - `tests/test_web_app.py:7802`
- 다음 Claude 슬라이스는 같은 family의 바로 아래 residual로 `operator_auditable_reviewed_memory_transition current-shipped wording truth sync`를 고정했습니다.

## 검증
- `sed -n '1,260p' work/4/9/2026-04-09-docs-source-message-vs-reviewed-memory-layer-shipped-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-boundary-defined-current-shipped-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1056,1064p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '796,804p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '583,590p'`
- `rg -n "later reviewed-memory|future reviewed memory|reviewed memory remains later|reviewed-memory layer|operator-visible local trace|operator_auditable_reviewed_memory_transition|trigger-source|emitted transition record|promotion and cross-session counting remain later" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1156,1162p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '886,891p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '663,667p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1529,1536p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '969,973p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '742,762p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '928,946p'`
- `nl -ba app/handlers/aggregate.py | sed -n '300,560p'`
- `nl -ba tests/test_web_app.py | sed -n '7284,7303p'`
- `nl -ba tests/test_web_app.py | sed -n '7484,7490p'`
- `nl -ba tests/test_web_app.py | sed -n '7641,7646p'`
- `nl -ba tests/test_web_app.py | sed -n '7800,7804p'`
- `git diff --check`
- Python unit test와 Playwright는 이번 검증 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- `operator_auditable_reviewed_memory_transition` 의미 줄이 root authority docs에서 아직 later-only처럼 읽혀, current shipped emitted/apply transition family와 충돌합니다.
