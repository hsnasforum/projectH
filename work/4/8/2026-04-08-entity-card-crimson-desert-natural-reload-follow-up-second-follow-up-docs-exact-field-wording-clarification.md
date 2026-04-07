# entity-card crimson-desert natural-reload follow-up + second-follow-up docs exact-field wording clarification

## 변경 파일

- `README.md` (line 166, 167)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1369, 1370)

## 사용 skill

- 없음 (docs-only exact-field wording clarification)

## 변경 이유

entity-card crimson-desert natural-reload follow-up/second-follow-up docs 4곳의 wording이 current test title(`e2e/tests/web-smoke.spec.mjs:5109`, `:5188`)의 compact exact-field pattern과 달리 장황한 풀어쓰기로 남아 있었습니다. same-family sibling docs와 동일한 parenthetical shorthand로 정렬하여 스캔성을 높였습니다.

## 핵심 변경

4곳 모두:
- `(출시일, 2025, blog.example.com)이 본문과 origin detail에 미노출되고` → `(출시일/2025/blog.example.com)이 미노출되고`
- `namu.wiki, ko.wikipedia.org continuity가 유지되고, context box에 blog.example.com provenance가 포함 유지` → `namu.wiki/ko.wikipedia.org/blog.example.com provenance continuity가 유지`

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- crimson-desert natural-reload follow-up/second-follow-up docs exact-field가 이번 라운드로 닫혔습니다.
- noisy single-source claim docs family 전체(click-reload initial + follow-up/second-follow-up, natural-reload follow-up/second-follow-up)가 모두 compact exact-field로 닫혔습니다.
- crimson-desert initial natural-reload docs의 exact-field도 이미 닫혀 있으므로, 현재 long-form docs 잔여는 없습니다.
