# entity-card dual-probe natural-reload docs browser-prefix wording clarification

## 변경 파일

- `README.md` (line 153, 154, 155, 156, 164)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1362, 1363, 1364, 1365, 1375)

## 사용 skill

- 없음 (docs-only browser-prefix clarification)

## 변경 이유

dual-probe natural-reload docs 10곳이 `browser 자연어 reload` framing을 direct prefix로 충분히 드러내지 않았습니다. sibling docs(`docs/MILESTONES.md:71-74`, `docs/TASK_BACKLOG.md:60-63`)는 이미 `browser natural-reload` framing을 사용하고 있으므로, README와 ACCEPTANCE_CRITERIA도 동일하게 맞췄습니다.

## 핵심 변경

10곳 모두 `자연어 reload` → `browser 자연어 reload` prefix 추가 (initial 4곳, follow-up 4곳, second-follow-up 2곳).

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- dual-probe natural-reload docs browser-prefix 전체(initial + follow-up + second-follow-up)가 이번 라운드로 닫혔습니다.
- 붉은사막/zero-strong-slot natural-reload docs도 이전 라운드에서 모두 닫혔습니다.
- latest-update natural-reload docs와 다른 family의 별도 패턴은 별도 라운드 대상입니다.
