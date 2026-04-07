# entity-card zero-strong-slot natural-reload source-path continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`

## 사용 skill
- 없음 (기존 테스트 assertion 추가 + docs truth-sync)

## 변경 이유
- zero-strong-slot natural-reload scenarios (38/39)가 response-origin continuity만 잠그고 있었고, source-path continuity(`namu.wiki`, `ko.wikipedia.org`)는 미잠금
- direct probe에서 자연어 reload와 follow-up 모두 `source_paths`에 두 URL이 유지되는 것을 확인

## 핵심 변경
1. **서비스 (natural reload)**: `test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` — `active_context.source_paths` assertion 추가
2. **서비스 (follow-up)**: `test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin` — `active_context.source_paths` assertion 추가
3. **브라우저 (scenario 38)**: `#context-box`에 `namu.wiki`, `ko.wikipedia.org` assertion 추가
4. **브라우저 (scenario 39)**: 동일 패턴으로 follow-up 후 context-box assertion 추가
5. **docs**: README 2곳, ACCEPTANCE_CRITERIA 2곳, MILESTONES 2곳 — scenarios 38/39에 source-path continuity 반영

## 검증
- `python3 -m unittest -v ...zero_strong_slot_entity_card_natural_reload_exact_fields ...zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin` → 2 tests OK (0.079s)
- `cd e2e && npx playwright test ... -g "entity-card zero-strong-slot 방금 검색한 결과 다시 보여줘..."` → 1 passed (7.6s)
- `cd e2e && npx playwright test ... -g "entity-card zero-strong-slot 자연어 reload 후 follow-up..."` → 1 passed (7.2s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- zero-strong-slot family의 source-path + response-origin continuity는 history-card 35/36 + natural-reload 38/39 모두 닫힘
- click-reload second follow-up 37의 source-path continuity는 별도 슬라이스 필요 시 추가
