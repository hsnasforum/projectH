# history-card latest-update single-source click-reload second-follow-up milestone/backlog response-origin exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 87)
- `docs/TASK_BACKLOG.md` (line 76)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `docs/MILESTONES.md:87`와 `docs/TASK_BACKLOG.md:76`는 `source-path + response-origin continuity`라는 generic framing을 사용하고 있었음
- current README:169, ACCEPTANCE:1378는 이미 source path 유지와 `WEB`, `최신 확인`, `단일 출처 참고`, `보조 출처` exact-field drift-prevention contract를 직접 드러내는 wording 사용 중
- 두 planning doc의 해당 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `MILESTONES.md:87`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`
- `TASK_BACKLOG.md:76`: `source-path + response-origin continuity` → `source-path + response-origin exact-field drift-prevention`

## 검증

- `nl -ba docs/MILESTONES.md | sed -n '87p'` → exact-field drift-prevention wording 확인
- `nl -ba docs/TASK_BACKLOG.md | sed -n '76p'` → exact-field drift-prevention wording 확인
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. 이번 라운드는 planning-doc wording만 다루었으며 runtime/README/ACCEPTANCE/browser smoke에는 변경 없음.
