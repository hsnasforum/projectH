# entity-card crimson-desert natural-reload initial docs exact-field wording clarification

## 변경 파일

- `README.md` (line 152, 158)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1361, 1367)

## 사용 skill

- 없음 (docs-only exact-field wording clarification)

## 변경 이유

entity-card crimson-desert natural-reload initial docs 4곳의 wording이 current test title의 compact exact-field pattern과 달리 long-form으로 남아 있었습니다. same-family follow-up/second-follow-up docs와 동일한 compact pattern으로 정렬하여 스캔성을 높였습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| README.md:152 | noisy claim을 `(출시일/2025/blog.example.com)` shorthand로, provenance를 `namu.wiki/ko.wikipedia.org/blog.example.com` compact path로 정렬 |
| README.md:158 | source path를 `namu.wiki/ko.wikipedia.org/blog.example.com` compact path로 정렬 |
| ACCEPTANCE_CRITERIA.md:1361 | noisy claim + provenance를 compact pattern으로 정렬 |
| ACCEPTANCE_CRITERIA.md:1367 | source path plurality를 compact path로 정렬 |

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- crimson-desert natural-reload initial docs exact-field가 이번 라운드로 닫혔습니다.
- crimson-desert natural-reload docs 전체(initial + follow-up + second-follow-up)가 모두 compact exact-field로 닫혔습니다.
