# entity-card zero-strong-slot natural-reload browser smoke truth sync

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — scenario 37 title 수정 ("자연어 reload" → "다시 불러오기 후 두 번째 follow-up")
- `README.md` — scenario 37 설명 수정, 서비스 테스트가 자연어 reload path를 별도로 커버한다는 사실 명시
- `docs/ACCEPTANCE_CRITERIA.md` — wording 정정
- `docs/MILESTONES.md` — wording 정정
- `docs/TASK_BACKLOG.md` — wording 정정
- `docs/NEXT_STEPS.md` — wording 정정

## 사용 skill

- 없음

## 변경 이유

- scenario 37의 title이 "자연어 reload"를 주장했지만, 실제 browser flow는 history-card `다시 불러오기` 클릭 후 `load_web_search_record_id` follow-up이었음
- browser에서 자연어 reload를 직접 테스트하려면 서버 세션에 web_search_history가 미리 등록되어야 하지만, pre-seeded record 방식으로는 불가능 (서버가 세션 history를 알지 못함)
- 서비스 테스트 `tests/test_web_app.py:15489-15563`이 자연어 reload path를 이미 잠그고 있으므로, browser smoke는 click-based path를 정직하게 반영하고 서비스 테스트가 natural reload를 별도 커버한다는 사실을 docs에 명시

## 핵심 변경

- scenario title: "자연어 reload 후 follow-up" → "다시 불러오기 후 두 번째 follow-up"
- docs 5개: wording을 click-based browser + natural-reload service로 분리 명시
- scenario count 변경 없음 (37 유지)

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` — 1 passed (6.8s)
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin` — OK (0.050s)

## 남은 리스크

- 없음 (truth-sync only)
