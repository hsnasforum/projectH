# entity-card zero-strong-slot click-reload second-follow-up source-path continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`

## 사용 skill
- 없음 (기존 테스트 assertion 추가 + 신규 서비스 테스트 + docs truth-sync)

## 변경 이유
- scenario 37 (zero-strong-slot click-reload second follow-up)이 response-origin continuity만 잠그고 있었고, source-path continuity(`namu.wiki`, `ko.wikipedia.org`)는 미잠금
- direct probe에서 second follow-up에서도 `source_paths`에 두 URL이 유지되는 것을 확인

## 핵심 변경
1. **서비스 (신규)**: `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths` — entity search → show-only reload → first follow-up → second follow-up 후 `active_context.source_paths` assertion
2. **브라우저 (scenario 37)**: `#context-box`에 `namu.wiki`, `ko.wikipedia.org` assertion 추가
3. **docs**: README 1곳, ACCEPTANCE_CRITERIA 1곳, MILESTONES 1곳 — scenario 37에 source-path continuity 반영

## 검증
- `python3 -m unittest -v ...zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths` → OK (0.070s)
- `cd e2e && npx playwright test ... -g "entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up..."` → 1 passed (7.4s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- zero-strong-slot family의 source-path + response-origin continuity는 history-card 35/36 + second-follow-up 37 + natural-reload 38/39 모두 닫힘
- zero-strong-slot family 전체 완료
