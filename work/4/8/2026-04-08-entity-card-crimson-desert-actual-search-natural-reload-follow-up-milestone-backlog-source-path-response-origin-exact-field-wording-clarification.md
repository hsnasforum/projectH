# entity-card 붉은사막 actual-search natural-reload follow-up milestone/backlog source-path + response-origin exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 75)
- `docs/TASK_BACKLOG.md` (line 64)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `MILESTONES.md:75`와 `TASK_BACKLOG.md:64`는 `source-path + response-origin continuity` generic framing 사용
- current README:157, ACCEPTANCE:1366는 이미 exact-field drift-prevention contract를 직접 드러내는 wording 사용 중
- 두 planning doc 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:75`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`
- `TASK_BACKLOG.md:64`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. planning-doc wording만 변경, runtime/README/ACCEPTANCE/browser smoke 무변경.
