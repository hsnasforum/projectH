# history-card entity-card noisy-single-source initial-click-reload browser-anchor provenance wording clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only wording clarification)

## 변경 이유
- history-card entity-card initial click-reload noisy-single-source browser anchor title이 generic `노출되지 않습니다` 수준이어서, 이미 검사 중인 `출시일`/`2025`/`blog.example.com` negative-assertion, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance contract가 title에서 드러나지 않았습니다.

## 핵심 변경
- test title에 `(출시일/2025/blog.example.com)` negative-assertion과 `설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다` 추가
- session ID에 `-prov` suffix 추가
- assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "history-card entity-card 다시 불러오기 후 noisy single-source claim"`: 1 passed
- `git diff --check`: clean

## 남은 리스크
- noisy-single-source family browser anchor provenance wording clarification은 initial/follow-up/second-follow-up × natural-reload/click-reload 전체 완료
- initial natural-reload exact-field browser anchor에 동일 wording clarification 필요 여부는 별도 확인 필요
