# history-card entity-card actual-entity-search response-origin truth-sync tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (기존 fixture/assertion truth-sync)

## 변경 이유
- history-card actual-search의 stored-record fixture와 browser pre-seeded record가 `verification_label: "설명형 단일 출처"`를 사용하고 있었으나, 현재 런타임은 two-result actual-search에서 `설명형 다중 출처 합의`를 emit
- 서비스 `store.save` fixture와 브라우저 pre-seeded record를 런타임 truth에 맞게 sync

## 핵심 변경
1. **서비스 테스트**: `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` — `store.save`의 `response_origin.verification_label`을 `설명형 다중 출처 합의`로 변경
2. **브라우저 smoke (scenario 48)**: `history-card entity-card 다시 불러오기 후 actual-search source path가 context box에 유지됩니다` — pre-seeded record와 history item의 `verification_label`을 `설명형 다중 출처 합의`로 변경
3. **브라우저 smoke (scenario 49)**: `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다` — pre-seeded record와 history item의 `verification_label`을 `설명형 다중 출처 합의`로 변경

## 검증
- `python3 -m unittest -v ...test_handle_chat_entity_card_reload_preserves_stored_response_origin ...test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → 2 tests OK (0.086s)
- `python3 -m unittest -v ...test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` → OK (0.033s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 actual-search source path가 context box에 유지됩니다"` → 1 passed (6.8s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다"` → 1 passed (6.6s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- actual-search history-card response-origin truth-sync는 show-only + follow-up 모두 닫힘
- 문서 시나리오 48/49는 source-path만 기술하므로 verification_label wording 변경 불필요
