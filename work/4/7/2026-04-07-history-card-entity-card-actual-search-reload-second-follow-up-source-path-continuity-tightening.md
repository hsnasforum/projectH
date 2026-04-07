# history-card entity-card actual-search reload second-follow-up source-path continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (신규 서비스 테스트 + 신규 브라우저 scenario + docs sync)

## 변경 이유
- actual-search click-reload second-follow-up에서 source-path + response-origin continuity가 잠기지 않았음
- direct probe에서 second follow-up에서도 두 URL이 유지되는 것을 확인

## 핵심 변경
1. **서비스 (신규)**: `test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_source_paths` — 4단계 flow 후 source_paths assertion
2. **브라우저 (scenario 50, 신규)**: `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path가 context box에 유지됩니다` — click reload → first follow-up → second follow-up 후 context-box + response-origin assertion
3. **docs**: scenario count 49→50, README 1곳, ACCEPTANCE_CRITERIA 1곳, MILESTONES 1곳, TASK_BACKLOG 1곳, NEXT_STEPS 1곳 동기화

## 검증
- `python3 -m unittest -v ...actual_entity_search_history_card_reload_second_follow_up_preserves_source_paths` → OK (0.072s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path가 context box에 유지됩니다"` → 1 passed (7.6s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- actual-search click-reload family는 show-only 48 + first follow-up 49 + second follow-up 50 모두 source-path + response-origin 닫힘
- dual-probe click-reload second-follow-up은 별도 슬라이스 필요 시 추가
