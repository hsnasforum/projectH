# history-card entity-card zero-strong-slot reload verification-label continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — entity-card zero-strong-slot reload verification-label continuity scenario 1건 추가 (scenario 35)
- `README.md` — scenario 35 추가
- `docs/ACCEPTANCE_CRITERIA.md` — zero-strong-slot reload verification-label continuity criteria 추가
- `docs/MILESTONES.md` — zero-strong-slot reload verification-label continuity browser smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 41 추가
- `docs/NEXT_STEPS.md` — scenario count 34→35 갱신, zero-strong-slot reload verification-label continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- 기존 entity-card reload smoke(scenario 17)는 strong-slot 있는 정상 entity-card만 다루고, zero-strong-slot variant의 downgraded verification label이 reload 후에도 과장 없이 유지되는지는 미검증
- service regression `tests/test_web_app.py:9047-9111`에서 exact-field reload continuity가 이미 잠겨 있으므로 browser contract만 추가
- header badge 렌더링(scenario 16의 card 4)에서 zero-strong-slot은 "검증 중" badge로 정적 렌더까지만 잠겨 있었고, click reload → response origin detail continuity는 비어 있었음

## 핵심 변경

- pre-seeded record: `answer_mode: "entity_card"`, `verification_label: "설명형 단일 출처"`, `source_roles: ["백과 기반"]`, zero-strong-slot (no strong claim coverage)
- 다시 불러오기 클릭 후 assert: `#response-origin-badge` = "WEB" + `.web`, `#response-answer-mode-badge` = "설명 카드", `#response-origin-detail`에 "설명형 단일 출처", "백과 기반" 포함

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields` — OK (0.035s) (기존 service test 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card zero-strong-slot 다시 불러오기 후 downgraded verification badge와 verification label이 유지됩니다" --reporter=line` — 1 passed (6.8s)
- `make e2e-test` — 생략 (shared browser helper 미변경, isolated rerun에서 drift 신호 없음)

## 남은 리스크

- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
