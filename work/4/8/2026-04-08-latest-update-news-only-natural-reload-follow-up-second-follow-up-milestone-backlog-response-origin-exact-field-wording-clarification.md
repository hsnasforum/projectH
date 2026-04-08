# latest-update news-only natural-reload follow-up-second-follow-up milestone/backlog response-origin exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 94)
- `docs/TASK_BACKLOG.md` (lines 85, 86)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `docs/MILESTONES.md:94`(combined line)와 `docs/TASK_BACKLOG.md:85-86`(split lines)는 `source-path + response-origin continuity`라는 generic framing을 사용하고 있었음
- current README:178-179, ACCEPTANCE:1387-1388는 이미 기사 source path 유지와 `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사` exact-field drift-prevention contract를 직접 드러내는 wording 사용 중
- 해당 3-line set을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:94`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`
- `TASK_BACKLOG.md:85`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`
- `TASK_BACKLOG.md:86`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`

## 검증

- `nl -ba docs/MILESTONES.md | sed -n '94p'` → exact-field drift-prevention wording 확인
- `nl -ba docs/TASK_BACKLOG.md | sed -n '85,86p'` → exact-field drift-prevention wording 확인
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. 이번 라운드는 planning-doc wording만 다루었으며 runtime/README/ACCEPTANCE/browser smoke에는 변경 없음.
