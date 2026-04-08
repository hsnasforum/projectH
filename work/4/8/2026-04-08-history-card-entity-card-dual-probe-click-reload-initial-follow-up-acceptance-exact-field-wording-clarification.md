# history-card entity-card dual-probe click-reload initial + follow-up acceptance exact-field wording clarification

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md` (lines 1344, 1352)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `ACCEPTANCE_CRITERIA.md:1344`는 `response-origin continuity` generic framing, source path도 구체 URL 없이 generic
- `ACCEPTANCE_CRITERIA.md:1352`는 `response-origin drift 없음` generic framing
- current README:135/143는 이미 `pearlabyss.com/200`, `pearlabyss.com/300` exact source path와 exact-field contract를 직접 드러내는 wording 사용 중
- 두 acceptance 라인을 동일한 exact-field drift-prevention framing으로 정렬

## 핵심 변경

- `ACCEPTANCE_CRITERIA.md:1344`: `response-origin continuity` + generic source path → `response-origin exact-field drift-prevention` + `pearlabyss.com/200`, `pearlabyss.com/300` exact path
- `ACCEPTANCE_CRITERIA.md:1352`: `response-origin drift 없음` → `response-origin exact-field drift 없음`

## 검증

- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 없음. acceptance wording만 변경, runtime/README/MILESTONES/TASK_BACKLOG/browser smoke 무변경.
