# history-card latest-update news-only click-reload follow-up milestone/backlog response-origin/source-path exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (lines 60, 64)
- `docs/TASK_BACKLOG.md` (lines 49, 53)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `MILESTONES.md:60`와 `TASK_BACKLOG.md:49`는 `response-origin continuity` generic framing 사용
- `MILESTONES.md:64`와 `TASK_BACKLOG.md:53`는 `source-path continuity` generic framing 사용
- current README:142/146, ACCEPTANCE:1351/1355는 이미 `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` exact-field contract를 직접 드러내는 wording 사용 중
- 4개 planning doc 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:60`: `response-origin continuity` → `response-origin exact-field drift-prevention`
- `MILESTONES.md:64`: `source-path continuity` → `source-path exact-field drift-prevention`
- `TASK_BACKLOG.md:49`: `response-origin continuity` → `response-origin exact-field drift-prevention`
- `TASK_BACKLOG.md:53`: `source-path continuity` → `source-path exact-field drift-prevention`

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. planning-doc wording만 변경, runtime/README/ACCEPTANCE/browser smoke 무변경.
