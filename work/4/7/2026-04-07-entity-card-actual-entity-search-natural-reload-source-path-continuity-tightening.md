# entity-card actual-entity-search natural-reload source-path continuity tightening

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
- actual entity-search (non-dual-probe) natural-reload 후 source path가 `active_context.source_paths`와 브라우저 `#context-box`에서 유지되는지 잠그는 서비스 회귀 + 브라우저 smoke가 없었음
- dual-probe source-path continuity는 이미 커버되어 있으나, generic actual-search path는 gap이었음

## 핵심 변경
1. **서비스 테스트**: `test_handle_chat_actual_entity_search_natural_reload_preserves_source_paths` — 붉은사막 entity search → `방금 검색한 결과 다시 보여줘` 자연어 reload 후 `active_context.source_paths`에 namu.wiki URL 유지 확인
2. **브라우저 smoke**: `entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다` — pre-seeded record 기반 button reload → natural reload 후 `#context-box`에 `namu.wiki` 텍스트 유지 확인
3. **docs**: scenario count 45→46, 5개 문서 동기화

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_preserves_source_paths` → OK (0.029s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다" --reporter=line` → 1 passed (6.8s)
- `rg` cross-check → 46 browser scenarios 일관
- `git diff --check` → whitespace error 없음

## 남은 리스크
- actual entity-search natural-reload follow-up source-path continuity는 이번 슬라이스 범위 밖 (핸드오프에서 명시적 제외)
- generic actual-search fixture가 단일 result URL만 emit하므로 source_paths에 하나만 잠김; 다중 result URL 보존은 별도 슬라이스 필요 시 추가
