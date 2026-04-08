# history-card entity-card actual-search click-reload initial + follow-up + second-follow-up acceptance exact-field wording clarification

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md` (lines 1371, 1372, 1373)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `ACCEPTANCE_CRITERIA.md:1371`는 `response-origin continuity` generic framing 사용
- `ACCEPTANCE_CRITERIA.md:1372-1373`는 `response-origin drift 없음` generic framing 사용
- current MILESTONES:80-82, TASK_BACKLOG:69-71, README:160-162는 이미 exact-field drift-prevention contract를 직접 드러내는 wording 사용 중
- 3개 acceptance 라인을 동일한 exact-field framing으로 정렬

## 핵심 변경

- `ACCEPTANCE_CRITERIA.md:1371`: `response-origin continuity` → `response-origin exact-field drift-prevention`
- `ACCEPTANCE_CRITERIA.md:1372`: `response-origin drift 없음` → `response-origin exact-field drift 없음`
- `ACCEPTANCE_CRITERIA.md:1373`: `response-origin drift 없음` → `response-origin exact-field drift 없음`

## 검증

- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 없음. acceptance wording만 변경, runtime/README/MILESTONES/TASK_BACKLOG/browser smoke 무변경.
