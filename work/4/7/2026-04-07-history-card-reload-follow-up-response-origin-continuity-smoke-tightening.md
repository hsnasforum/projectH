# history-card reload follow-up stored response-origin continuity smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+100 lines)

## 사용 skill
- 없음

## 변경 이유
- service regression `tests/test_web_app.py:14840-14932`는 entity-card 검색 후 `load_web_search_record_id + user_text` follow-up에서 stored `response_origin`이 drift하지 않아야 한다고 이미 잠그고 있었지만, Playwright smoke에는 대응 scenario가 없었음
- 같은 history-card reload family 안에서 가장 좁은 browser-visible current-risk reduction 1건

## 핵심 변경
1. 새 Playwright scenario 추가: "history-card 다시 불러오기 후 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다"
2. pre-seeded record에 stored `response_origin`(`answer_mode: "entity_card"`, `verification_label`, `source_roles` 포함) 설정
3. 다시 불러오기 (show-only) 후 `sendRequest({user_text, load_web_search_record_id})` follow-up을 page.evaluate로 실행
4. follow-up 후 `#response-origin-badge` (WEB), `#response-answer-mode-badge` (설명 카드), `#response-origin-detail` (설명형 단일 출처, 백과 기반) continuity assertion 3건

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card 다시 불러오기 후 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`: 1 passed (7.3s)
- `make e2e-test`: 생략 (single-scenario Playwright tightening, shared helper 변경 없음)
- `python3 -m unittest -v tests.test_web_app`: 생략 (Playwright test-only tightening, Python 코드 변경 없음)

## 남은 리스크
- `make e2e-test` full suite는 이번 라운드에서 실행하지 않았음; shared helper를 건드리지 않았으므로 isolated rerun으로 충분하다고 판단했지만, 다음 라운드에서 broader regression 확인 필요
- pre-seeded record의 `response_origin`은 runtime이 생성하는 origin과 동일한 field를 직접 설정하므로, runtime origin 구조가 바뀌면 fixture도 함께 갱신해야 함
