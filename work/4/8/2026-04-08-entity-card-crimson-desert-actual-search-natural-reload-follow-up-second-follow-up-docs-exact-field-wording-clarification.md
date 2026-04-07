# entity-card crimson-desert actual-search natural-reload follow-up + second-follow-up docs exact-field wording clarification

## 변경 파일

- `README.md` (line 157, 159, 165)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1366, 1368, 1376)

## 사용 skill

- 없음 (docs-only exact-field wording clarification)

## 변경 이유

crimson-desert actual-search natural-reload follow-up/second-follow-up docs 6곳의 wording이 current test title의 compact combined source-path + response-origin pattern과 달리 분리되거나 long-form으로 남아 있었습니다. source-path를 `/` separator compact path로 정렬하고, response-origin follow-up line에 source-path를 통합했습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| README.md:157 | response-origin만 있던 line에 source path(`namu.wiki`/`ko.wikipedia.org`) 통합 |
| README.md:159 | source path `, ` separator → `/` separator |
| README.md:165 | source path `, ` separator → `/` separator, badge wording compact화 |
| ACCEPTANCE_CRITERIA.md:1366 | source path(`namu.wiki`/`ko.wikipedia.org`) 통합 추가 |
| ACCEPTANCE_CRITERIA.md:1368 | `plurality` 제거, `/` separator |
| ACCEPTANCE_CRITERIA.md:1376 | `, ` separator → `/` separator |

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- crimson-desert actual-search natural-reload follow-up/second-follow-up docs exact-field가 이번 라운드로 닫혔습니다.
- crimson-desert natural-reload docs 전체(initial + noisy + actual-search follow-up/second-follow-up)가 모두 compact exact-field로 정렬됐습니다.
