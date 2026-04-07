# entity-card noisy single-source claim natural-reload docs browser-prefix wording clarification

## 변경 파일

- `README.md` (line 184, 185)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1393, 1394)

## 사용 skill

- 없음 (docs-only browser-prefix clarification)

## 변경 이유

entity-card noisy single-source claim natural-reload follow-up/second-follow-up docs 4곳이 `browser 자연어 reload` framing을 direct prefix로 충분히 드러내지 않았습니다. sibling docs(`docs/MILESTONES.md:97`, `docs/TASK_BACKLOG.md:91-92`)와 current browser smoke test title(`e2e/tests/web-smoke.spec.mjs:6244`, `:6317`)은 이미 browser framing을 사용하고 있으므로, README와 ACCEPTANCE_CRITERIA도 동일하게 맞췄습니다.

## 핵심 변경

4곳 모두 `자연어 reload 후` → `browser 자연어 reload 후` prefix 추가.

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- natural-reload docs browser-prefix family 전체(zero-strong-slot + crimson-desert + dual-probe + latest-update + noisy single-source claim)가 이번 라운드로 모두 닫혔습니다.
- noisy single-source claim click-reload docs의 별도 패턴은 별도 라운드 대상입니다.
