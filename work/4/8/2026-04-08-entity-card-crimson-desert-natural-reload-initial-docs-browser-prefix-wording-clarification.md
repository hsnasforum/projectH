# entity-card crimson-desert natural-reload initial docs browser-prefix wording clarification

## 변경 파일

- `README.md` (line 152, 158)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1361, 1367)

## 사용 skill

- 없음 (docs-only browser-prefix clarification)

## 변경 이유

붉은사막 initial natural-reload docs 4곳이 `browser 자연어 reload` framing을 direct prefix로 충분히 드러내지 않았습니다. sibling docs(`docs/MILESTONES.md:70`, `docs/MILESTONES.md:76`, `docs/TASK_BACKLOG.md:59`, `docs/TASK_BACKLOG.md:65`)는 이미 `browser natural-reload` framing을 사용하고 있으므로, README와 ACCEPTANCE_CRITERIA도 동일하게 맞췄습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| README.md:152 | `자연어 reload에서` → `browser 자연어 reload에서` |
| README.md:158 | `자연어 reload에서` → `browser 자연어 reload에서` |
| ACCEPTANCE_CRITERIA.md:1361 | `자연어 reload` → `browser 자연어 reload` |
| ACCEPTANCE_CRITERIA.md:1367 | `자연어 reload` → `browser 자연어 reload` |

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 붉은사막 initial natural-reload docs browser-prefix는 이번 라운드로 닫혔습니다.
- 붉은사막 follow-up/dual-probe docs의 동일 패턴과 다른 family의 별도 docs 패턴은 별도 라운드 대상입니다.
