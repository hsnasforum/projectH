# history-card latest-update single-source click-reload initial milestone/backlog verification-label/source-path exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (lines 55, 58)
- `docs/TASK_BACKLOG.md` (lines 44, 47)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `MILESTONES.md:55`와 `TASK_BACKLOG.md:44`는 `verification-label continuity` generic framing 사용
- `MILESTONES.md:58`와 `TASK_BACKLOG.md:47`은 `source-path continuity` generic framing 사용
- current README:137/140, ACCEPTANCE:1346/1349는 이미 `단일 출처 참고`, `보조 출처`, `example.com/seoul-weather` exact-field contract를 직접 드러내는 wording 사용 중
- 4개 planning doc 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:55`: `verification-label continuity` → `verification-label exact-field drift-prevention`
- `MILESTONES.md:58`: `source-path continuity` → `source-path exact-field drift-prevention`
- `TASK_BACKLOG.md:44`: `verification-label continuity` → `verification-label exact-field drift-prevention`
- `TASK_BACKLOG.md:47`: `source-path continuity` → `source-path exact-field drift-prevention`

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. planning-doc wording만 변경, runtime/README/ACCEPTANCE/browser smoke 무변경.
