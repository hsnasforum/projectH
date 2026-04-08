# history-card latest-update single-source click-reload second-follow-up acceptance exact-field wording clarification

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md` (line 1378)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `ACCEPTANCE_CRITERIA.md:1378`는 `response-origin drift 없음` generic framing 사용
- current README:169, MILESTONES:87, TASK_BACKLOG:76는 이미 exact-field drift-prevention contract를 직접 드러내는 wording 사용 중
- acceptance 라인을 동일한 exact-field framing으로 정렬

## 핵심 변경

- `ACCEPTANCE_CRITERIA.md:1378`: `response-origin drift 없음` → `response-origin exact-field drift 없음`

## 검증

- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 없음. acceptance wording만 변경, runtime/README/MILESTONES/TASK_BACKLOG/browser smoke 무변경.
