# Docs NEXT_STEPS TASK_BACKLOG claim-coverage current-behavior summary sync

## 변경 파일

- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

`docs/NEXT_STEPS.md:15`는 claim-coverage를 `status tags and actionable hints`까지만 기술, `docs/TASK_BACKLOG.md:24`는 `slot reinvestigation scaffolding`이라는 구 문구를 사용하고 있어, 같은 파일 내 인접 상세 라인(line 16, 25)이 이미 focus-slot reinvestigation explanation을 반영한 것과 내부 불일치가 있었음.

## 핵심 변경

### docs/NEXT_STEPS.md
- line 15: `claim-coverage panel with status tags and actionable hints` → `claim-coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation (improved/regressed/unchanged)`

### docs/TASK_BACKLOG.md
- line 24: `Claim coverage panel with status tags and actionable hints, and slot reinvestigation scaffolding` → `Claim coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation (improved/regressed/unchanged)`

## 검증

- `rg -n "slot reinvestigation scaffolding" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`: 0건 확인
- `rg -n "focus-slot reinvestigation explanation" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md README.md docs/PRODUCT_SPEC.md`: 전체 일관성 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- claim-coverage 관련 문서 동기화는 이제 전체 문서 계층에서 완료됨. `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md` 포함 모든 레벨 동기화 완료.
