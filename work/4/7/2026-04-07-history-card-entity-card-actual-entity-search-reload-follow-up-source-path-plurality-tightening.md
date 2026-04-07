# history-card entity-card actual-entity-search reload follow-up source-path plurality tightening

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
- 기존 follow-up click reload source-path continuity 테스트가 `namu.wiki` 하나만 잠그고 있었으나, 구현은 이미 다중 URL(`namu.wiki` + `ko.wikipedia.org`)을 보존하고 있었음
- 새 시나리오 추가 없이 기존 assertion을 확장하여 follow-up plurality를 명시적으로 잠그는 것이 목표

## 핵심 변경
1. **서비스 테스트**: `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` — `assertIn` ko.wikipedia URL 추가 (fixture에는 이미 두 URL 포함)
2. **브라우저 smoke**: 기존 scenario 49 — `await expect(contextBox).toContainText("ko.wikipedia.org")` assertion 추가
3. **docs**: scenario count 변경 없이 wording에 `ko.wikipedia.org` 반영 (README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG)

## 검증
- `python3 -m unittest -v ...test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` → OK (0.030s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다"` → 1 passed (6.9s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- actual-search reload family의 source-path plurality는 show-only + follow-up 모두 닫힘
- natural-reload family의 plurality 확장은 별도 슬라이스 필요 시 추가
