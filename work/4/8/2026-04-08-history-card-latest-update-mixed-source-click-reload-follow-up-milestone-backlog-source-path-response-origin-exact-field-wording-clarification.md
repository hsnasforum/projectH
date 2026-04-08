# history-card latest-update mixed-source click-reload follow-up milestone/backlog source-path + response-origin exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 62)
- `docs/TASK_BACKLOG.md` (line 51)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `MILESTONES.md:62`와 `TASK_BACKLOG.md:51`는 `source-path + response-origin continuity` generic framing 사용
- current README:144, ACCEPTANCE:1353는 이미 exact-field drift-prevention contract를 직접 드러내는 wording 사용 중
- 두 planning doc 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:62`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`
- `TASK_BACKLOG.md:51`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. planning-doc wording만 변경, runtime/README/ACCEPTANCE/browser smoke 무변경.
