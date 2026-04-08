# entity-card 붉은사막 actual-search natural-reload second-follow-up milestone/backlog response-origin exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 85)
- `docs/TASK_BACKLOG.md` (line 74)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `docs/MILESTONES.md:85`와 `docs/TASK_BACKLOG.md:74`는 `source-path + response-origin continuity`라는 generic framing을 사용하고 있었음
- current README:165, ACCEPTANCE:1376는 이미 source path 유지와 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` exact-field drift-prevention contract를 직접 드러내는 wording 사용 중
- 두 planning doc의 해당 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:85`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`
- `TASK_BACKLOG.md:74`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`

## 검증

- `nl -ba docs/MILESTONES.md | sed -n '85p'` → exact-field drift-prevention wording 확인
- `nl -ba docs/TASK_BACKLOG.md | sed -n '74p'` → exact-field drift-prevention wording 확인
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. 이번 라운드는 planning-doc wording만 다루었으며 runtime/README/ACCEPTANCE/browser smoke에는 변경 없음.
