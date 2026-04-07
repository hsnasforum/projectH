# entity-card actual-entity-search natural-reload follow-up source-path continuity tightening

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
- actual entity-search natural-reload 후 follow-up(`이 검색 결과 요약해줘` + `load_web_search_record_id`)에서 source path가 `active_context.source_paths`와 브라우저 `#context-box`에 유지되는지 잠그는 서비스 회귀 + 브라우저 smoke가 없었음
- show-only source-path continuity는 직전 round에서 닫혔고, 이번은 follow-up까지 연장한 gap 보완

## 핵심 변경
1. **서비스 테스트**: `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths` — 붉은사막 entity search → 자연어 reload → follow-up 후 `active_context.source_paths`에 namu.wiki URL 유지 확인
2. **브라우저 smoke**: `entity-card 붉은사막 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다` — pre-seeded record 기반 button reload → natural reload → follow-up 후 `#context-box`에 `namu.wiki` 유지 확인
3. **docs**: scenario count 46→47, 5개 문서 동기화

## 검증
- `python3 -m unittest -v ...test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths` → OK (0.046s)
- `cd e2e && npx playwright test ... -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다"` → 1 passed (6.9s)
- `rg` cross-check → 47 browser scenarios 일관
- `git diff --check` → whitespace error 없음

## 남은 리스크
- entity-card natural-reload family의 actual-search 변형 source-path continuity는 show-only + follow-up 모두 닫힘
- 다중 result URL 보존(현재 fixture는 단일 namu.wiki URL만 emit)은 별도 슬라이스 필요 시 추가
