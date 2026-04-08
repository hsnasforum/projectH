# Docs README PRODUCT_SPEC claim-coverage current-behavior explanation sync

## 변경 파일

- `README.md`
- `docs/PRODUCT_SPEC.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 이미 claim-coverage panel의 focus-slot reinvestigation explanation을 반영했으나, 상위 현재-동작 요약 문서인 `README.md:69`와 `docs/PRODUCT_SPEC.md:106,154,310`은 여전히 status tags + actionable hints까지만, 또는 `slot reinvestigation scaffolding`으로 기술하고 있어 내부 불일치가 있었음.

## 핵심 변경

### README.md
- 기능 요약 불릿(line 69)에 `dedicated plain-language focus-slot reinvestigation explanation (improved/regressed/unchanged)` 추가

### docs/PRODUCT_SPEC.md
- line 106: 상위 feature summary에 focus-slot reinvestigation explanation 추가
- line 154: Web Investigation 지원 설명에 `focus-slot reinvestigation explanation` 추가
- line 310: Web Investigation Rules Implemented에서 `slot reinvestigation scaffolding` → `dedicated plain-language focus-slot reinvestigation explanation (improved/regressed/unchanged)` 교체

## 검증

- `rg -n "claim coverage panel|focus-slot reinvestigation explanation|slot reinvestigation scaffolding" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`: `slot reinvestigation scaffolding` 없음 확인, 모든 문서 `focus-slot reinvestigation explanation` 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md` 등 planning docs에는 이번 동기화 범위에 포함하지 않았음.
