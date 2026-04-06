# general-chat transcript timestamp smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+2 lines)

## 사용 skill
- 없음 (단일 파일 2줄 추가)

## 변경 이유
- `일반 채팅 응답에는 source-type label이 붙지 않습니다` scenario는 major browser flow 이후 lighter scenario 중 transcript/conversation timeline path에 가장 가깝고 scope가 가장 작은 first unprotected flow였음
- core chat-mode browser flow로서 `response-text` direct gate와 transcript-meta probe를 이미 재사용하므로 timestamp assertion을 additive하게 얹기에 적합

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs` general-chat scenario 끝(982줄 직전)에 transcript `.message-when` first/last regex assertion 2개 추가
- assertion shape: `/오[전후]\s\d{1,2}:\d{2}/` (earlier scenarios와 동일)

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright tightening, Python 코드 변경 없음)

## 남은 리스크
- cancel scenario는 partial stream timing이 섞여 별도 판단 필요
- claim-coverage, web-search history badges는 transcript message path가 아니라 helper/render path
- history-card reload는 secondary web mode라 범위가 더 큼
