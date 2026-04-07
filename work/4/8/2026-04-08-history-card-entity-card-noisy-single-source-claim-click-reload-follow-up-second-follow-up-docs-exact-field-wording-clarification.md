# history-card entity-card noisy single-source claim click-reload follow-up + second-follow-up docs exact-field wording clarification

## 변경 파일

- `README.md` (line 186, 187)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1395, 1396)

## 사용 skill

- 없음 (docs-only exact-field wording clarification)

## 변경 이유

history-card entity-card noisy single-source claim click-reload follow-up/second-follow-up docs 4곳의 wording이 current test title(`e2e/tests/web-smoke.spec.mjs:6393`, `:6462`)의 compact exact-field pattern(`출시일/2025/blog.example.com` 미노출 + `namu.wiki/ko.wikipedia.org/blog.example.com` provenance)과 달리 장황한 풀어쓰기로 남아 있었습니다. test title과 동일한 parenthetical shorthand로 정렬하여 스캔성을 높였습니다.

## 핵심 변경

4곳 모두:
- `본문과 origin detail에 출시일, 2025, blog.example.com 미노출되고` → `(출시일/2025/blog.example.com) 미노출되고`
- `namu.wiki, ko.wikipedia.org 유지, context box에는 blog.example.com provenance 포함 유지` → `namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지`

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- noisy single-source claim docs family(natural-reload + click-reload) 전체가 이번 라운드로 닫혔습니다.
- 전체 browser-anchor wording clarification + docs browser-prefix + docs exact-field family가 모두 닫혔습니다.
