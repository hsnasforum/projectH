# entity-card noisy single-source claim natural-reload follow-up + second-follow-up docs exact-field wording clarification

## 변경 파일

- `README.md` (line 184, 185)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1393, 1394)

## 사용 skill

- 없음 (docs-only exact-field wording clarification)

## 변경 이유

entity-card noisy single-source claim natural-reload follow-up/second-follow-up docs 4곳의 wording이 current test title과 current click-reload docs의 compact exact-field pattern과 달리 장황한 풀어쓰기로 남아 있었습니다. click-reload sibling docs(`README.md:186-187`, `ACCEPTANCE_CRITERIA.md:1395-1396`)와 동일한 parenthetical shorthand로 정렬하여 스캔성을 높였습니다.

## 핵심 변경

4곳 모두:
- `본문과 origin detail에 출시일, 2025, blog.example.com 미노출되고` → `(출시일/2025/blog.example.com) 미노출되고`
- `namu.wiki, ko.wikipedia.org 유지, context box에는 blog.example.com provenance 포함 유지` → `namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지`

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- noisy single-source claim docs family(natural-reload + click-reload) exact-field wording이 이번 라운드로 모두 닫혔습니다.
- 전체 browser-anchor wording clarification + docs browser-prefix + docs exact-field family가 모두 닫혔습니다.
