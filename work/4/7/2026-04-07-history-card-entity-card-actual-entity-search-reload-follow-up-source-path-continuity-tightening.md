# history-card entity-card actual-entity-search reload follow-up source-path continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (패턴 재사용 기반 수동 구현)

## 변경 이유
- generic actual-search entity-card를 history-card `다시 불러오기`(click reload)로 불러온 뒤 follow-up(`이 검색 결과 요약해줘` + `load_web_search_record_id`)에서 source path가 `active_context.source_paths`와 브라우저 `#context-box`에 유지되는지 잠그는 서비스 회귀 + 브라우저 smoke가 없었음
- show-only click reload source-path continuity는 직전 round에서 닫혔고, 이번은 follow-up까지 연장한 gap 보완

## 핵심 변경
1. **서비스 테스트**: `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` — `WebSearchStore`에 직접 저장한 actual-search record → `load_web_search_record_id` reload → follow-up 후 `active_context.source_paths`에 namu.wiki URL 유지 확인
2. **브라우저 smoke**: `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다` — pre-seeded record `다시 불러오기` click → follow-up 후 `#context-box`에 `namu.wiki` 유지 확인
3. **docs**: scenario count 48→49, 5개 문서 동기화

## 검증
- `python3 -m unittest -v ...test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` → OK (0.032s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다"` → 1 passed (6.8s)
- `rg` cross-check → 49 browser scenarios 일관
- `git diff --check` → whitespace error 없음

## 남은 리스크
- history-card entity-card actual-search reload family의 source-path continuity는 show-only + follow-up 모두 닫힘
- generic actual-search fixture는 단일 namu.wiki URL만 emit; 다중 URL 보존은 별도 슬라이스 필요 시 추가
