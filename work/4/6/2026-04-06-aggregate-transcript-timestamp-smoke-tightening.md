# same-session recurrence aggregate transcript timestamp smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+2 lines)

## 사용 skill
- 없음 (단일 파일 2줄 추가)

## 변경 이유
- `same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다` scenario는 per-message timestamp contract를 아직 smoke에서 잠그지 않은 마지막 unprotected later flow였음
- 이전 라운드들에서 corrected-save family 2건과 candidate confirmation 1건을 닫았으므로, 남은 aggregate 1건을 잠그면 transcript timestamp smoke family가 완결됨

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs` aggregate scenario 끝(950줄 직전)에 transcript `.message-when` first/last regex assertion 2개 추가
- assertion shape: `/오[전후]\s\d{1,2}:\d{2}/` (earlier scenarios와 동일)

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright tightening, Python 코드 변경 없음)

## 남은 리스크
- 이번 라운드로 모든 major browser flow scenario에 transcript `.message-when` first/last assertion이 추가됨
- cancel, general chat, claim-coverage, web-search history, history-reload 등 lighter scenario는 transcript message가 적거나 timestamp 렌더링 경로가 다를 수 있어 별도 판단 필요
