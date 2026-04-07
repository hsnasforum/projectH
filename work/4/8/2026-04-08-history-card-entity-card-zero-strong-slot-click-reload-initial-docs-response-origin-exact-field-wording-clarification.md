# history-card entity-card zero-strong-slot click-reload initial docs response-origin exact-field wording clarification

## 변경 파일

- `README.md` (line 147)
- `docs/MILESTONES.md` (line 65)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1356)
- `docs/TASK_BACKLOG.md` (line 54)

## 사용 skill

- 없음 (docs-only exact-field clarification)

## 변경 이유

zero-strong-slot initial click-reload docs 4곳이 `설명 카드`, `설명형 단일 출처`, `백과 기반`, source path는 적고 있었지만 `WEB` origin badge truth를 직접 드러내지 않았습니다. same family test/body는 이미 `WEB` origin까지 직접 고정하고 있으므로(`e2e/tests/web-smoke.spec.mjs:3682`, `:3757`), docs도 동일하게 맞췄습니다.

## 핵심 변경

4곳 모두 `WEB` origin badge (또는 `WEB` badge + `response-origin` scope) 명시 추가.

## 검증

- `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- zero-strong-slot click-reload docs set(initial + follow-up)은 이번 라운드로 모두 닫혔습니다.
- 다른 family의 별도 docs 패턴은 별도 라운드 대상입니다.
