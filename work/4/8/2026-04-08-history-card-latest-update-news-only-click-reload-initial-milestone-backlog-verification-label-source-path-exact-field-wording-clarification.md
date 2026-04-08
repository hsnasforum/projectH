# history-card latest-update news-only click-reload initial milestone/backlog verification-label/source-path exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (lines 56, 57)
- `docs/TASK_BACKLOG.md` (lines 45, 46)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `MILESTONES.md:56`와 `TASK_BACKLOG.md:45`는 `verification-label continuity` generic framing 사용
- `MILESTONES.md:57`와 `TASK_BACKLOG.md:46`은 `source-path continuity` generic framing 사용
- current README:138/139, ACCEPTANCE:1347/1348는 이미 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` exact-field contract를 직접 드러내는 wording 사용 중
- 4개 planning doc 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:56`: `verification-label continuity` → `verification-label exact-field drift-prevention`
- `MILESTONES.md:57`: `source-path continuity` → `source-path exact-field drift-prevention`
- `TASK_BACKLOG.md:45`: `verification-label continuity` → `verification-label exact-field drift-prevention`
- `TASK_BACKLOG.md:46`: `source-path continuity` → `source-path exact-field drift-prevention`

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. planning-doc wording만 변경, runtime/README/ACCEPTANCE/browser smoke 무변경.
