# history-card entity-card actual-entity-search reload source-path continuity tightening

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
- generic actual-search entity-card를 history-card `다시 불러오기`(click reload, `load_web_search_record_id`)로 불러왔을 때 source path가 `active_context.source_paths`와 브라우저 `#context-box`에 유지되는지 잠그는 서비스 회귀 + 브라우저 smoke가 없었음
- dual-probe click reload source-path continuity는 이미 커버되어 있으나, generic actual-search path는 gap이었음

## 핵심 변경
1. **서비스 테스트**: `test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths` — 붉은사막 entity search → `load_web_search_record_id` reload 후 `active_context.source_paths`에 namu.wiki URL 유지 확인
2. **브라우저 smoke**: `history-card entity-card 다시 불러오기 후 actual-search source path가 context box에 유지됩니다` — pre-seeded record 기반 `다시 불러오기` click 후 `#context-box`에 `namu.wiki` 유지 확인
3. **docs**: scenario count 47→48, 5개 문서 동기화

## 검증
- `python3 -m unittest -v ...test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths` → OK (0.032s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 actual-search source path가 context box에 유지됩니다"` → 1 passed (6.8s)
- `rg` cross-check → 48 browser scenarios 일관
- `git diff --check` → whitespace error 없음

## 남은 리스크
- history-card click reload follow-up source-path continuity는 이번 슬라이스 범위 밖
- generic actual-search fixture는 단일 namu.wiki URL만 emit; 다중 URL 보존은 별도 슬라이스 필요 시 추가
