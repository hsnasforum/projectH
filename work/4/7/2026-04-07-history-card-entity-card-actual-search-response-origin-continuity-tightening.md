# history-card entity-card actual-search response-origin continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (기존 테스트에 assertion 추가)

## 변경 이유
- history-card actual-search click-reload/follow-up tests/scenarios (48/49)가 source-path plurality만 잠그고 있었고, response-origin continuity(`entity_card`, `설명형 다중 출처 합의`, `백과 기반`)는 잠기지 않았음
- 자연어 reload path에는 이미 response-origin continuity anchor가 있으므로, click-reload path에도 같은 truth를 얹는 bounded tightening

## 핵심 변경
1. **서비스 (show-only reload)**: `test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths` — `response_origin` exact fields assertion 추가 (`entity_card`, `설명형 다중 출처 합의`, `["백과 기반"]`)
2. **서비스 (follow-up)**: `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` — `response_origin` exact fields assertion 추가
3. **브라우저 (scenario 48)**: `#response-answer-mode-badge` (`설명 카드`), `#response-origin-detail` (`설명형 다중 출처 합의`, `백과 기반`) assertion 추가
4. **브라우저 (scenario 49)**: 동일 패턴으로 follow-up 후 response-origin continuity assertion 추가

## 검증
- `python3 -m unittest -v ...actual_entity_search_reload_preserves_active_context_source_paths ...entity_card_actual_search_follow_up_preserves_source_paths ...actual_entity_search_natural_reload_follow_up_preserves_response_origin` → 3 tests OK (0.113s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 actual-search source path가 context box에 유지됩니다"` → 1 passed (7.4s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다"` → 1 passed (7.1s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- history-card actual-search family의 source-path + response-origin continuity는 show-only + follow-up 모두 닫힘
- zero-strong-slot family, latest-update family의 truth-sync는 별도 슬라이스 필요 시 추가
