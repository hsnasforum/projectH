# history-card latest-update single-source follow-up response-origin continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_latest_update_single_source_reload_follow_up_preserves_stored_response_origin` 추가
- `e2e/tests/web-smoke.spec.mjs` — latest-update single-source follow-up response-origin continuity scenario 1건 추가 (scenario 29)
- `README.md` — scenario 29 추가
- `docs/ACCEPTANCE_CRITERIA.md` — single-source follow-up drift prevention criteria 추가
- `docs/MILESTONES.md` — single-source follow-up continuity service + browser smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 35 추가
- `docs/NEXT_STEPS.md` — scenario count 28→29 갱신, single-source follow-up continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- 기존 follow-up continuity는 mixed-source(`공식+기사 교차 확인` + `보조 기사`·`공식 기반`)만 service(`tests/test_web_app.py:14935-15012`)와 browser(`e2e/tests/web-smoke.spec.mjs:1449-1571`)에서 잠겨 있고, single-source variant는 미검증
- single-source show-only reload의 verification-label/source-path continuity는 scenario 25/28에서 이미 잠갔으나 follow-up path는 비어 있었음

## 핵심 변경

- **서비스 테스트**: single-source latest_update 검색 → `load_web_search_record_id + user_text` follow-up에서 `answer_mode = "latest_update"`, `verification_label = "단일 출처 참고"`, `source_roles = ["보조 출처"]` exact-field 유지 assert
- **브라우저 smoke**: pre-seeded single-source record → 다시 불러오기 → follow-up 전송 → `#response-origin-badge` = "WEB", `#response-answer-mode-badge` = "최신 확인", `#response-origin-detail`에 "단일 출처 참고", "보조 출처" 포함 assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_follow_up_preserves_stored_response_origin` — OK (0.029s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` — 1 passed (6.7s)
- `make e2e-test` — 생략 (shared browser helper 미변경, isolated rerun에서 drift 신호 없음)

## 남은 리스크

- news-only follow-up variant는 별도 라운드 대상
- full Python regression suite 미실행 (isolated 1건만 확인) — broader regression 가능성 잔존하나 기존 fixture 재사용이므로 위험 낮음
