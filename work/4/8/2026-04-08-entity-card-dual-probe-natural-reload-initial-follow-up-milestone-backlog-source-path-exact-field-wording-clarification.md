# entity-card dual-probe natural-reload initial + follow-up milestone/backlog source-path exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (lines 71, 73)
- `docs/TASK_BACKLOG.md` (lines 60, 62)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 4줄 모두 `source-path continuity` generic framing 사용
- current README:153/155, ACCEPTANCE:1362/1364는 이미 exact source path와 exact-field drift-prevention contract를 직접 드러내는 wording 사용 중
- 4개 planning doc 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:71`: `source-path continuity` → `source-path exact-field drift-prevention`
- `MILESTONES.md:73`: `source-path continuity` → `source-path exact-field drift-prevention`
- `TASK_BACKLOG.md:60`: `source-path continuity` → `source-path exact-field drift-prevention`
- `TASK_BACKLOG.md:62`: `source-path continuity` → `source-path exact-field drift-prevention`

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. planning-doc wording만 변경, runtime/README/ACCEPTANCE/browser smoke 무변경.
