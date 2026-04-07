# entity-card noisy single-source claim natural-reload follow-up + second-follow-up exact-field provenance wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 6244, 6317)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

entity-card noisy single-source claim natural-reload follow-up/second-follow-up title 2개가 positive-retention truth(`설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`)를 title에서 직접 드러내지 못했습니다. 기존 title은 `본문과 origin detail에 미노출되고 blog.example.com provenance가 context box에 유지`만 표현했지만, body에서 실제로 검증하는 exact-field와 provenance plurality를 완전히 반영하도록 맞췄습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 6244 | `…본문과 origin detail에 미노출되고 blog.example.com provenance가 context box에 유지됩니다` | `…미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다` |
| line 6317 | `…본문과 origin detail에 미노출되고 blog.example.com provenance가 context box에 유지됩니다` | `…미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim.*자연어 reload 후" --reporter=line` → 2 passed (13.6s)

## 남은 리스크

- entity-card noisy single-source claim natural-reload follow-up/second-follow-up family(2 anchors)는 이번 라운드로 닫혔습니다.
- history-card entity-card click-reload noisy single-source claim family와 다른 answer-mode family(zero-strong-slot, crimson 등)의 동일 패턴은 별도 라운드 대상입니다.
