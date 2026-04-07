# entity-card crimson-desert natural-reload second-follow-up docs browser-prefix wording clarification

## 변경 파일

- `README.md` (line 165, 167)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1370)

## 사용 skill

- 없음 (docs-only browser-prefix clarification)

## 변경 이유

붉은사막 natural-reload second-follow-up docs 3곳이 `browser 자연어 reload 후 두 번째 follow-up` framing을 direct prefix로 충분히 드러내지 않았습니다. sibling docs(`docs/MILESTONES.md:79`, `docs/TASK_BACKLOG.md:68`)는 이미 `browser natural-reload` framing을 사용하고 있으므로, README와 ACCEPTANCE_CRITERIA도 동일하게 맞췄습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| README.md:165 | `actual-search 자연어 reload 후 두 번째` → `actual-search browser 자연어 reload 후 두 번째` |
| README.md:167 | `붉은사막 자연어 reload 후 두 번째` → `붉은사막 browser 자연어 reload 후 두 번째` |
| ACCEPTANCE_CRITERIA.md:1370 | `붉은사막 자연어 reload 후 두 번째` → `붉은사막 browser 자연어 reload 후 두 번째` |

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 붉은사막 natural-reload docs browser-prefix 전체(initial + follow-up + second-follow-up)가 이번 라운드로 닫혔습니다.
- dual-probe docs의 동일 패턴은 별도 라운드 대상입니다.
