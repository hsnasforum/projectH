# history-card latest-update mixed-source click-reload initial milestone/backlog source-path + response-origin exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 54)
- `docs/TASK_BACKLOG.md` (line 43)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `docs/MILESTONES.md:54`와 `docs/TASK_BACKLOG.md:43`는 `source-path + response-origin continuity`라는 generic framing을 사용하고 있었음
- current README:136, ACCEPTANCE:1345는 이미 source path 유지와 `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` exact-field contract를 직접 드러내는 wording 사용 중
- 두 planning doc의 해당 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:54`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`
- `TASK_BACKLOG.md:43`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. planning-doc wording만 변경, runtime/README/ACCEPTANCE/browser smoke 무변경.
