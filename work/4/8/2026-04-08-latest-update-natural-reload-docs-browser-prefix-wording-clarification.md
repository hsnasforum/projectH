# latest-update natural-reload docs browser-prefix wording clarification

## 변경 파일

- `README.md` (line 171-181, 11곳)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1380-1390, 11곳)

## 사용 skill

- 없음 (docs-only browser-prefix clarification)

## 변경 이유

latest-update mixed-source/single-source/news-only/noisy-community natural-reload docs 22곳이 `browser 자연어 reload` framing을 direct prefix로 충분히 드러내지 않았습니다. sibling docs(`docs/MILESTONES.md:89-95`, `docs/TASK_BACKLOG.md:78-88`)와 current browser smoke test title은 이미 `browser natural-reload` framing을 사용하고 있으므로, README와 ACCEPTANCE_CRITERIA도 동일하게 맞췄습니다.

## 핵심 변경

22곳 모두 `자연어 reload` → `browser 자연어 reload` prefix 추가.
- mixed-source: initial 1 + follow-up 1 + second-follow-up 1 = 3곳 × 2 files = 6
- single-source: initial 1 + follow-up 1 + second-follow-up 1 = 3곳 × 2 files = 6
- news-only: initial 1 + follow-up 1 + second-follow-up 1 = 3곳 × 2 files = 6
- noisy-community: follow-up 1 + second-follow-up 1 = 2곳 × 2 files = 4

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- latest-update natural-reload docs browser-prefix 전체(mixed/single/news/noisy)가 이번 라운드로 닫혔습니다.
- natural-reload docs browser-prefix family 전체(zero-strong-slot + crimson-desert + dual-probe + latest-update)가 모두 닫혔습니다.
- entity-card noisy single-source claim natural-reload/click-reload docs의 별도 패턴은 별도 라운드 대상입니다.
