# history-card entity-card zero-strong-slot source-path continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`

## 사용 skill
- 없음 (기존 테스트 assertion 추가 + docs truth-sync)

## 변경 이유
- zero-strong-slot history-card scenarios (35/36)가 response-origin continuity만 잠그고 있었고, source-path continuity(`namu.wiki`, `ko.wikipedia.org`)는 미잠금
- direct probe에서 reload/follow-up 모두 `source_paths`에 두 URL이 유지되는 것을 확인

## 핵심 변경
1. **서비스 (reload)**: `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields` — `active_context.source_paths` assertion 추가 (`namu.wiki/testgame`, `ko.wikipedia.org/testgame`)
2. **서비스 (follow-up)**: `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_follow_up_preserves_stored_response_origin` — `active_context.source_paths` assertion 추가
3. **브라우저 (scenario 35)**: `#context-box`에 `namu.wiki`, `ko.wikipedia.org` assertion 추가
4. **브라우저 (scenario 36)**: 동일 패턴으로 follow-up 후 context-box assertion 추가
5. **docs**: README 2곳, ACCEPTANCE_CRITERIA 2곳, MILESTONES 2곳 — scenarios 35/36에 source-path continuity 반영

## 검증
- `python3 -m unittest -v ...zero_strong_slot_entity_card_history_card_reload_exact_fields ...zero_strong_slot_entity_card_history_card_reload_follow_up_preserves_stored_response_origin` → 2 tests OK (0.075s)
- `cd e2e && npx playwright test ... -g "history-card entity-card zero-strong-slot 다시 불러오기 후 설명 카드..."` → 1 passed (7.5s)
- `cd e2e && npx playwright test ... -g "history-card entity-card zero-strong-slot 다시 불러오기 후 follow-up..."` → 1 passed (7.1s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- zero-strong-slot history-card family의 source-path + response-origin continuity는 show-only + follow-up 모두 닫힘
- scenario 37 (second follow-up), natural-reload 38/39의 source-path continuity는 별도 슬라이스 필요 시 추가
