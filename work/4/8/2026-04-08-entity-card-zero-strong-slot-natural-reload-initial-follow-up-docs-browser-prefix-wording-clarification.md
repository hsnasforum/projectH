# entity-card zero-strong-slot natural-reload initial + follow-up docs browser-prefix wording clarification

## 변경 파일

- `README.md` (line 150, 151)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1359, 1360)

## 사용 skill

- 없음 (docs-only browser-prefix clarification)

## 변경 이유

zero-strong-slot natural-reload initial/follow-up docs 4곳이 `browser natural-reload` path라는 framing을 direct prefix로 충분��� 드러내지 않았습니다. sibling docs(`docs/MILESTONES.md:68-69`, `docs/TASK_BACKLOG.md:57-58`)는 이미 `browser natural-reload` framing을 사용하고 있으므로, README와 ACCEPTANCE_CRITERIA도 동일하게 맞췄습니다. ACCEPTANCE_CRITERIA line 1360의 후행 `(browser natural-reload path)` suffix도 불필요하게 되어 제거했습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| README.md:150 | `자연어 reload` → `browser 자연어 reload` |
| README.md:151 | `자연어 reload 후 follow-up…(browser natural-reload path)` → `browser 자연어 reload 후 follow-up…` (suffix 제거) |
| ACCEPTANCE_CRITERIA.md:1359 | `자연어 reload` → `browser 자연어 reload` |
| ACCEPTANCE_CRITERIA.md:1360 | `자연어 reload 후 follow-up…(browser natural-reload path)` → `browser 자연어 reload 후 follow-up…` (suffix 제거) |

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- zero-strong-slot docs set(click-reload + natural-reload) 전체가 이번 라운드로 닫혔습니다.
- 다른 family의 별도 docs 패턴은 별도 라운드 대상입니다.
