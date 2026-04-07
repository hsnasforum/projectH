# entity-card crimson-desert natural-reload follow-up docs browser-prefix wording clarification

## 변경 파일

- `README.md` (line 157, 159, 166)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1366, 1368, 1369)

## 사용 skill

- 없음 (docs-only browser-prefix clarification)

## 변경 이유

붉은사막 natural-reload follow-up docs 6곳이 `browser 자연어 reload 후 follow-up` framing을 direct prefix로 충분히 드러내지 않았습니다. sibling docs(`docs/MILESTONES.md:75,77,78`, `docs/TASK_BACKLOG.md:64,66,67`)는 이미 `browser natural-reload` framing을 사용하고 있으므로, README와 ACCEPTANCE_CRITERIA도 동일하게 맞췄습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| README.md:157 | `actual-search 자연어 reload 후` → `actual-search browser 자연어 reload 후` |
| README.md:159 | `actual-search 자연어 reload 후` → `actual-search browser 자연어 reload 후` |
| README.md:166 | `붉은사막 자연어 reload 후` → `붉은사막 browser 자연어 reload 후` |
| ACCEPTANCE_CRITERIA.md:1366 | `actual-search 자연어 reload 후` → `actual-search browser 자연어 reload 후` |
| ACCEPTANCE_CRITERIA.md:1368 | `actual-search 자연어 reload 후` → `actual-search browser 자연어 reload 후` |
| ACCEPTANCE_CRITERIA.md:1369 | `붉은사막 자연어 reload 후` → `붉은사막 browser 자연어 reload 후` |

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 붉은사막 natural-reload follow-up docs browser-prefix는 이번 라운드로 닫혔습니다.
- dual-probe docs의 동일 패턴과 second-follow-up/noisy exclusion docs의 별도 패턴은 별도 라운드 대상입니다.
