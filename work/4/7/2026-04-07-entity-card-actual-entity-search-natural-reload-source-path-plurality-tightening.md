# entity-card actual-entity-search natural-reload source-path plurality tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (기존 테스트 assertion 확장)

## 변경 이유
- natural-reload family의 show-only와 follow-up source-path continuity 테스트가 `namu.wiki` 하나만 잠그고 있었으나, 구현은 이미 다중 URL(`namu.wiki` + `ko.wikipedia.org`)을 보존하고 있었음
- show-only + follow-up을 한 coherent slice로 묶어 plurality를 명시적으로 잠그는 것이 목표

## 핵심 변경
1. **서비스 테스트 (show-only)**: `test_handle_chat_actual_entity_search_natural_reload_preserves_source_paths` — fixture를 two-result로 확장, `assertIn` ko.wikipedia URL 추가
2. **서비스 테스트 (follow-up)**: `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths` — fixture를 two-result로 확장, `assertIn` ko.wikipedia URL 추가
3. **브라우저 smoke (show-only)**: scenario 46 — `toContainText("ko.wikipedia.org")` assertion 추가 (record에는 이미 두 결과가 pre-seeded)
4. **브라우저 smoke (follow-up)**: scenario 47 — `toContainText("ko.wikipedia.org")` assertion 추가
5. **docs**: scenario count 변경 없이 wording에 `ko.wikipedia.org` 반영 (README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG)

## 검증
- `python3 -m unittest -v ...natural_reload_preserves_source_paths ...natural_reload_follow_up_preserves_source_paths` → 2 tests OK (0.074s)
- `cd e2e && npx playwright test ... -g "entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다"` → 1 passed (6.8s)
- `cd e2e && npx playwright test ... -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다"` → 1 passed (6.6s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- actual-search source-path plurality는 click-reload + natural-reload 모두 show-only + follow-up 닫힘
- 이 family의 plurality tightening은 완료
