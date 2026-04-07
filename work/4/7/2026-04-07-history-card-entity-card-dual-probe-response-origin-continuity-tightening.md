# history-card entity-card dual-probe response-origin continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`

## 사용 skill
- 없음 (기존 테스트 assertion 추가 + docs truth-sync)

## 변경 이유
- history-card dual-probe click-reload/follow-up scenarios (23/31)가 source-path continuity만 잠그고 있었고, response-origin continuity(`entity_card`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반`)는 미잠금
- 자연어 reload path에는 이미 response-origin continuity anchor가 있으므로, click-reload path에도 같은 truth를 얹는 bounded tightening

## 핵심 변경
1. **서비스 (follow-up)**: `test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths` — `response_origin` exact fields assertion 추가 (`entity_card`, `설명형 다중 출처 합의`, `["공식 기반", "백과 기반"]`)
2. **브라우저 (scenario 23)**: `#response-answer-mode-badge` (`설명 카드`), `#response-origin-detail` (`설명형 다중 출처 합의`, `공식 기반`, `백과 기반`) assertion 추가
3. **브라우저 (scenario 31)**: 동일 패턴으로 follow-up 후 response-origin continuity assertion 추가
4. **docs**: README 2곳, ACCEPTANCE_CRITERIA 2곳, MILESTONES 2곳 — scenarios 23/31에 response-origin continuity 반영

## 검증
- `python3 -m unittest -v ...dual_probe_entity_search_history_card_reload_exact_fields ...entity_card_dual_probe_follow_up_preserves_source_paths` → 2 tests OK (0.072s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 dual-probe source path가 context box에 유지됩니다"` → 1 passed (7.5s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다"` → 1 passed (7.1s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- history-card dual-probe family의 source-path + response-origin continuity는 show-only + follow-up 모두 닫힘
- zero-strong-slot family, latest-update family의 truth-sync는 별도 슬라이스 필요 시 추가
