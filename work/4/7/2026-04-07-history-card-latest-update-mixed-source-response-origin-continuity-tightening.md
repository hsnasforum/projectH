# history-card latest-update mixed-source response-origin continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`

## 사용 skill
- 없음 (기존 테스트 assertion 추가 + docs truth-sync)

## 변경 이유
- history-card latest-update mixed-source click-reload/follow-up scenarios (24/32)가 source-path continuity만 잠그고 있었고, response-origin continuity(`latest_update`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반`)는 미잠금
- service anchor 테스트(`test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields`, `test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin`)는 이미 잠겨 있으나, follow-up source-path 테스트에는 response_origin 미확인

## 핵심 변경
1. **서비스 (follow-up)**: `test_handle_chat_latest_update_mixed_source_follow_up_preserves_source_paths` — `response_origin` exact fields assertion 추가 (`latest_update`, `공식+기사 교차 확인`, `["보조 기사", "공식 기반"]`)
2. **브라우저 (scenario 24)**: `최신 확인` answer-mode badge, `공식+기사 교차 확인`, `보조 기사`, `공식 기반` origin detail assertion 추가
3. **브라우저 (scenario 32)**: 동일 패턴으로 follow-up 후 response-origin continuity assertion 추가
4. **docs**: README 2곳, ACCEPTANCE_CRITERIA 2곳, MILESTONES 2곳 — scenarios 24/32에 response-origin continuity 반영

## 검증
- `python3 -m unittest -v ...mixed_source_latest_update_exact_fields ...latest_update_reload_follow_up_preserves_stored_response_origin ...latest_update_mixed_source_follow_up_preserves_source_paths` → 3 tests OK (0.077s)
- `cd e2e && npx playwright test ... -g "history-card latest-update 다시 불러오기 후 mixed-source source path가 context box에 유지됩니다"` → 1 passed (7.5s)
- `cd e2e && npx playwright test ... -g "history-card latest-update mixed-source 다시 불러오기 후 follow-up 질문에서 source path가 context box에 유지됩니다"` → 1 passed (6.9s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- history-card latest-update mixed-source family의 source-path + response-origin continuity는 show-only + follow-up 모두 닫힘
- single-source, news-only latest-update source-path scenarios의 response-origin continuity는 별도 슬라이스 필요 시 추가
