# history-card entity-card zero-strong-slot click-reload initial + follow-up + second-follow-up milestone/backlog exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (lines 65, 66, 67)
- `docs/TASK_BACKLOG.md` (lines 54, 55, 56)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 6줄 모두 `response-origin + source-path continuity` generic framing 사용
- current README:147-149, ACCEPTANCE:1356-1358는 이미 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` exact-field contract를 직접 드러내는 wording 사용 중
- 6개 planning doc 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:65`: `continuity` → `exact-field drift-prevention`
- `MILESTONES.md:66`: `continuity` → `exact-field drift-prevention`
- `MILESTONES.md:67`: `continuity` → `exact-field drift-prevention`
- `TASK_BACKLOG.md:54`: `continuity` → `exact-field drift-prevention`
- `TASK_BACKLOG.md:55`: `continuity` → `exact-field drift-prevention`
- `TASK_BACKLOG.md:56`: `continuity` → `exact-field drift-prevention`

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. planning-doc wording만 변경, runtime/README/ACCEPTANCE/browser smoke 무변경.
