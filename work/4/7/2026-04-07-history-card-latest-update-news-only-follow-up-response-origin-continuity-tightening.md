# history-card latest-update news-only follow-up response-origin continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_latest_update_news_only_reload_follow_up_preserves_stored_response_origin` 추가
- `e2e/tests/web-smoke.spec.mjs` — latest-update news-only follow-up response-origin continuity scenario 1건 추가 (scenario 30)
- `README.md` — scenario 30 추가
- `docs/ACCEPTANCE_CRITERIA.md` — news-only follow-up drift prevention criteria 추가
- `docs/MILESTONES.md` — news-only follow-up continuity service + browser smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 36 추가
- `docs/NEXT_STEPS.md` — scenario count 29→30 갱신, news-only follow-up continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- 기존 follow-up continuity는 mixed-source와 single-source만 service+browser에서 잠겨 있고, news-only variant는 미검증
- news-only show-only reload의 verification-label/source-path continuity는 scenario 26/27에서 이미 잠갔으나 follow-up path는 비어 있었음

## 핵심 변경

- **서비스 테스트**: news-only latest_update 검색(hankyung+mk) → `load_web_search_record_id + user_text` follow-up에서 `answer_mode = "latest_update"`, `verification_label = "기사 교차 확인"`, `source_roles = ["보조 기사"]` exact-field 유지 assert
- **브라우저 smoke**: pre-seeded news-only record → 다시 불러오기 → follow-up 전송 → `#response-origin-badge` = "WEB", `#response-answer-mode-badge` = "최신 확인", `#response-origin-detail`에 "기사 교차 확인", "보조 기사" 포함 assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_follow_up_preserves_stored_response_origin` — OK (0.028s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` — 1 passed (6.7s)
- `make e2e-test` — 생략 (shared browser helper 미변경, isolated rerun에서 drift 신호 없음)

## 남은 리스크

- full Python regression suite 미실행 (isolated 1건만 확인) — broader regression 가능성 잔존하나 기존 fixture 재사용이므로 위험 낮음
- history-card reload follow-up family가 mixed/single/news 3개 variant 모두 service+browser로 잠겼으므로 이 family의 remaining risk는 매우 낮음
