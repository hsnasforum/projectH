# history-card entity-card noisy single-source claim click-reload initial docs exact-field wording clarification

## 변경 파일

- `README.md` (line 134)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1343)

## 사용 skill

- 없음 (docs-only exact-field wording clarification)

## 변경 이유

history-card entity-card noisy single-source claim click-reload initial docs 2곳의 wording이 current test title(`e2e/tests/web-smoke.spec.mjs:1701`)의 compact exact-field pattern과 달리 장황한 풀어쓰기로 남아 있었습니다. same-family follow-up/second-follow-up docs처럼 parenthetical shorthand와 compact provenance path로 정렬했습니다. agreement-backed 사실 카드(`확인된 사실:`, `교차 확인`) 유지 truth는 보존했습니다.

## 핵심 변경

2곳 모두:
- `(출시일, 2025, blog.example.com)이 본문과 origin detail에 노출되지 않고` → `(출시일/2025/blog.example.com)이 미노출되고`
- `context box에 namu.wiki, ko.wikipedia.org, blog.example.com provenance 포함 확인` → `namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지`

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- noisy single-source claim click-reload initial docs가 이번 라운드로 닫혔습니다.
- crimson-desert natural-reload follow-up/second-follow-up long-form docs(`README.md:166-167`, `ACCEPTANCE_CRITERIA.md:1369-1370`)가 아직 남아 있습니다.
