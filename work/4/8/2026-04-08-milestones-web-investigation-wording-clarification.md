# MILESTONES Web Investigation wording clarification

## 변경 파일

- `docs/MILESTONES.md`

## 사용 skill

- 없음 (문서 전용 슬라이스)

## 변경 이유

`docs/MILESTONES.md:7`의 Current Product 프레이밍이 `Web investigation remains a secondary mode.`로만 되어 있어 출하된 permission states(enabled/disabled/ask)와 document-first guardrail을 반영하지 못하고 있었음. 같은 계열의 다른 root-level 문서들은 모두 이미 정렬 완료된 상태.

## 핵심 변경

1. **Current Product (line 7)**: `Web investigation remains a secondary mode.` → `Web investigation remains a permission-gated secondary mode (enabled/disabled/ask per session) under the document-first guardrail.`
   - milestone 수준의 간결함 유지하면서 핵심 두 가지(permission states, document-first guardrail)만 추가

## 검증

- `git diff -- docs/MILESTONES.md`: 1줄 교체 확인
- `git diff --check -- docs/MILESTONES.md`: whitespace 에러 없음
- `nl -ba docs/MILESTONES.md | sed -n '5,12p'`: 핵심 라인 정렬 확인 완료

## 남은 리스크

- 이 슬라이스로 웹 조사 문구 정렬 계열의 모든 root-level 문서가 정렬 완료됨: `TASK_BACKLOG`, `README`, `PRODUCT_SPEC`, `ACCEPTANCE_CRITERIA`, `NEXT_STEPS`, `project-brief`, `PRODUCT_PROPOSAL`, `MILESTONES`.
- 같은 계열의 추가 리스크 없음. 다음 슬라이스는 Codex가 새로운 계열을 선택할 차례.
