# latest-update noisy-community natural-reload follow-up + second-follow-up exclusion exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 5965, 6034)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

latest-update noisy-community natural-reload follow-up/second-follow-up title 2개가 generic wording(`origin detail과 본문에 다시 노출되지 않습니다`)만 남아 있어, body에서 이미 검증하는 negative exclusion(`보조 커뮤니티`, `brunch` 미노출)과 positive retention(`기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` 유지)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 5965 | `…follow-up에서도 origin detail과 본문에 다시 노출되지 않습니다` | `…follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다` |
| line 6034 | `…두 번째 follow-up에서도 origin detail과 본문에 다시 노출되지 않습니다` | `…두 번째 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update noisy community source가 자연어 reload 후" --reporter=line` → 2 passed (14.5s)

## 남은 리스크

- latest-update noisy-community natural-reload follow-up/second-follow-up family(2 anchors)는 이번 라운드로 닫혔습니다.
- click-reload noisy-community family와 다른 answer-mode family(zero-strong-slot, crimson, entity-card actual-search natural-reload 등)의 동일 패턴은 별도 라운드 대상입니다.
