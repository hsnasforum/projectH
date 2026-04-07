# history-card entity-card noisy-single-source click-reload follow-up/second-follow-up browser-anchor provenance wording clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only wording clarification)

## 변경 이유
- history-card click-reload noisy-single-source follow-up/second-follow-up browser anchor titles가 `다시 노출되지 않습니다` 수준이어서, 이미 검사 중인 `출시일`/`2025`/`blog.example.com` negative-assertion과 `blog.example.com` provenance contract가 title에서 드러나지 않았습니다.
- docs와 service anchors는 이 contract를 직접 명시합니다.

## 핵심 변경
- 2개 test title에 `(출시일/2025/blog.example.com)` negative-assertion과 `blog.example.com provenance가 context box에 유지됩니다` 추가
- 2개 session ID에 `-prov` suffix 추가
- assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "history-card entity-card noisy single-source claim"`: 2 passed
- `git diff --check`: clean

## 남은 리스크
- noisy-single-source family의 모든 browser anchor (natural-reload + click-reload) provenance wording clarification 완료
