# latest-update noisy-community natural-reload follow-up-second-follow-up milestone wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 95)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `docs/MILESTONES.md:95`는 generic `negative assertion with ... positive assertion` framing을 사용하고 있었음
- current TASK_BACKLOG:87-88, README:180-181, ACCEPTANCE:1389-1390는 이미 `negative in origin detail, response body, context box + ... positive retention` exclusion contract를 직접 드러내는 wording 사용 중
- MILESTONES combined line을 동일한 exclusion exact-field framing으로 정렬
- TASK_BACKLOG:87-88는 이미 직접적 표현을 사용 중이므로 수정하지 않음

## 핵심 변경

- `MILESTONES.md:95`: `negative assertion with ... positive assertion` → `negative in origin detail, response body, context box + ... positive retention`

## 검증

- `nl -ba docs/MILESTONES.md | sed -n '95p'` → exclusion exact-field wording 확인
- `nl -ba docs/TASK_BACKLOG.md | sed -n '87,88p'` → 기존 직접적 표현 유지 확인
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. 이번 라운드는 MILESTONES wording만 다루었으며 runtime/README/ACCEPTANCE/browser smoke에는 변경 없음.
