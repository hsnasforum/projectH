# Docs README MILESTONES TASK_BACKLOG claim-coverage smoke inventory truth sync

## 변경 파일

- `README.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md`와 `docs/NEXT_STEPS.md`는 이미 claim-coverage panel의 focus-slot reinvestigation explanation (improved/regressed/unchanged) smoke 커버리지를 반영했으나, `README.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 여전히 leading status tags + actionable hints까지만 기술하고 있어 문서 간 내부 불일치가 있었음.

## 핵심 변경

### README.md
- 시나리오 15번 claim-coverage 설명에 `focus-slot reinvestigation explanation (improved/regressed/unchanged with natural Korean particle normalization)` 추가

### docs/MILESTONES.md
- Playwright smoke suite claim-coverage inventory에 `focus-slot reinvestigation explanation including improved/regressed/unchanged with natural Korean particle normalization` 추가

### docs/TASK_BACKLOG.md
- Playwright smoke coverage claim-coverage inventory에 동일 문구 추가

## 검증

- `rg -n "focus-slot reinvestigation explanation" README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`: 5개 파일 모두 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 향후 smoke 시나리오 추가 시 5개 문서의 inventory가 다시 drift할 수 있음.
