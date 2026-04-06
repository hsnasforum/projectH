# history-card latest-update follow-up response-origin continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin` 추가
- `e2e/tests/web-smoke.spec.mjs` — latest-update follow-up response-origin continuity scenario 1건 추가 (scenario 20)
- `README.md` — scenario 20 추가
- `docs/ACCEPTANCE_CRITERIA.md` — latest-update follow-up drift 없음 criteria 추가
- `docs/MILESTONES.md` — latest-update follow-up smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 26 추가
- `docs/NEXT_STEPS.md` — scenario count 19→20 갱신, latest-update follow-up 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- entity-card follow-up drift prevention은 service(`tests/test_web_app.py:14840-14932`)와 browser(`e2e/tests/web-smoke.spec.mjs:1332-1447`)에 이미 존재하지만, latest-update variant는 양쪽 모두 비어 있었음
- latest-update show-only reload는 service(`test_handle_chat_mixed_source_latest_update_reload_exact_fields`)와 browser(scenario 18)로 잠겨 있지만, follow-up 경로의 response_origin exact-field continuity는 미검증

## 핵심 변경

- **서비스 테스트**: mixed-source latest_update 검색 → `load_web_search_record_id + user_text` follow-up에서 `answer_mode = "latest_update"`, `verification_label = "공식+기사 교차 확인"`, `source_roles = ["보조 기사", "공식 기반"]` exact-field 유지 assert
- **브라우저 smoke**: pre-seeded latest_update record → 다시 불러오기 → follow-up 전송 → `#response-origin-badge` = "WEB", `#response-answer-mode-badge` = "최신 확인", `#response-origin-detail`에 "공식+기사 교차 확인", "보조 기사", "공식 기반" 포함 assert
- **문서 sync**: 5개 문서에 scenario 20 반영, count 19→20

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin` — OK (0.033s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` — 1 passed (6.7s)
- `make e2e-test` — 생략 (shared browser helper 미변경, isolated rerun에서 drift 신호 없음)

## 남은 리스크

- noisy community host exclusion variant는 별도 라운드 대상
- full Python regression suite 미실행 (isolated 1건만 확인) — broader regression 가능성 잔존하나 기존 fixture 재사용이므로 위험 낮음
