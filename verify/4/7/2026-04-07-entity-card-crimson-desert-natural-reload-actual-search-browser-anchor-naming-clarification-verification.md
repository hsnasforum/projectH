# entity-card crimson-desert natural-reload actual-search browser-anchor naming clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-browser-anchor-naming-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson natural-reload actual-search browser anchor naming을 정리했고, family 전체 정렬이 끝났다고 주장했습니다. 이번 라운드에서는 그 test-only naming change 자체와 completion 서술이 actual browser fixture truth까지 맞는지 다시 확인할 필요가 있었습니다.
- rerun 결과 [e2e/tests/web-smoke.spec.mjs:4870](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4870), [e2e/tests/web-smoke.spec.mjs:4990](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4990), [e2e/tests/web-smoke.spec.mjs:5045](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5045)의 browser test title과 [e2e/tests/web-smoke.spec.mjs:4871](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4871), [e2e/tests/web-smoke.spec.mjs:4991](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4991), [e2e/tests/web-smoke.spec.mjs:5046](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5046)의 session id naming 보정은 current tree와 일치했고, isolated Playwright rerun도 `3 passed`였습니다.
- 다만 follow-up source-path browser fixture는 still actual-search branch truth보다 약합니다. [e2e/tests/web-smoke.spec.mjs:4873](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4873)의 comment는 여전히 `single source`를 말하고, seeded record/historical metadata인 [e2e/tests/web-smoke.spec.mjs:4905](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4905), [e2e/tests/web-smoke.spec.mjs:4935](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4935)는 still `설명형 단일 출처`를 넣습니다. 반면 paired service anchors인 [tests/test_web_app.py:16443](/home/xpdlqj/code/projectH/tests/test_web_app.py:16443), [tests/test_web_app.py:16511](/home/xpdlqj/code/projectH/tests/test_web_app.py:16511), [tests/test_web_app.py:16582](/home/xpdlqj/code/projectH/tests/test_web_app.py:16582)는 actual entity-search branch를 일관되게 `설명형 다중 출처 합의` family로 다룹니다.

## 핵심 변경
- latest `/work`를 partial-truth로 판정했습니다. browser test title/session-id naming correction, `git diff --check` clean, filtered Playwright rerun `3 passed`, scenario count `75` 주장은 current tree와 일치했습니다.
- 다만 `/work`의 `crimson natural-reload actual-search family 전체 정렬 완료` 및 `남은 리스크 없음`은 과장입니다. source-path follow-up browser fixture comment와 seeded verification label/history metadata가 아직 single-source wording에 머물러 있습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert natural-reload actual-search source-path browser fixture truth-sync correction`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-browser-anchor-naming-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-actual-search-response-origin-docs-wording-clarification-verification.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4868,5055p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4238,4338p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4868,4942p'`
- `rg -n "entity-card 붉은사막 actual-search 자연어 reload 후|entity-actual-search-natural-reload-followup-sp|entity-actual-search-natural-reload-followup-origin|entity-actual-search-natural-reload-second-followup-origin" e2e/tests/web-smoke.spec.mjs`
- `rg -n '설명형 단일 출처|single source|generic entity_card record|entity-actual-search-natural-reload-followup-sp|entity-actual-search-natural-reload' e2e/tests/web-smoke.spec.mjs`
- `rg -n 'actual entity-search|설명형 다중 출처 합의|설명형 단일 출처' tests/test_web_app.py | sed -n '1,120p'`
- `rg -n "entity-actual-search-natural-reload-followup-sp|entity-actual-search-natural-reload-followup-origin|entity-actual-search-natural-reload-second-followup-origin|test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths|test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin|test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_response_origin_and_source_paths" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 좁은 browser-anchor verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 follow-up source-path browser fixture truth mismatch입니다. [e2e/tests/web-smoke.spec.mjs:4873](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4873), [e2e/tests/web-smoke.spec.mjs:4905](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4905), [e2e/tests/web-smoke.spec.mjs:4935](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4935)가 actual-search branch naming으로 바뀐 title/session-id와 달리 still single-source wording을 남깁니다.
- 반면 initial natural-reload actual-search exact-field anchor인 [e2e/tests/web-smoke.spec.mjs:4242](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4242)와 paired service anchors는 multi-source agreement branch를 직접 가리킵니다. 따라서 다음 라운드는 runtime을 건드리지 않고 `e2e/tests/web-smoke.spec.mjs`의 follow-up source-path browser fixture comment, seeded `verification_label`, rendered history metadata를 `설명형 다중 출처 합의` actual-search truth로 맞추는 test-only correction이 가장 작고 reviewable합니다.
