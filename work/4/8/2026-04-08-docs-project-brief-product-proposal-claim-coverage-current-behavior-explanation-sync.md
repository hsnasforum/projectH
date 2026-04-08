# Docs project-brief PRODUCT_PROPOSAL claim-coverage current-behavior explanation sync

## 변경 파일

- `docs/project-brief.md`
- `docs/PRODUCT_PROPOSAL.md`

## 사용 skill

- 없음

## 변경 이유

`README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 모두 claim-coverage panel의 focus-slot reinvestigation explanation을 반영했으나, root-doc layer인 `docs/project-brief.md:81`과 `docs/PRODUCT_PROPOSAL.md:61`은 여전히 `status tags and actionable hints`까지만 기술하고 있었음.

## 핵심 변경

### docs/project-brief.md
- line 81: `claim coverage panel with status tags and actionable hints` → `claim coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation (improved/regressed/unchanged)`

### docs/PRODUCT_PROPOSAL.md
- line 61: 동일 문구 교체

## 검증

- `rg -n "status tags and actionable hints" docs/project-brief.md docs/PRODUCT_PROPOSAL.md`: 0건 (구 문구 제거 확인)
- `rg -n "focus-slot reinvestigation explanation" docs/project-brief.md docs/PRODUCT_PROPOSAL.md README.md docs/PRODUCT_SPEC.md`: 전체 일관성 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- claim-coverage 관련 문서 동기화는 이번 슬라이스로 전체 문서 계층에서 완료됨.
