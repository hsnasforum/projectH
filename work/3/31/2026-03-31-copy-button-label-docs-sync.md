# 2026-03-31 copy-path button label docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 3곳의 copy button label을 구체화했으나 docs에 미반영하여 verify에서 `not_ready`

## 핵심 변경

### docs 반영 (3개 파일)
- `README.md`: copy button label을 실제 UI text로 나열 (`응답 복사`, `저장 경로 복사`, `승인 경로 복사`, `검색 기록 경로 복사`, `검색 기록 복사`)
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: "purpose-specific labels" 명시 + 동일 label 나열

### 변경하지 않은 것
- 코드 변경 없음
- 테스트 변경 없음
- `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`: milestone state 변경 없음이므로 미수정

## 검증
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
