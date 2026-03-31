# 2026-03-31 note-path placeholder coverage docs sync

## 변경 파일
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 note-path placeholder contract의 unit test + E2E assertion을 추가했으나, 이 coverage truth를 docs에 반영하지 않아 verify에서 `not_ready`

## 핵심 변경

### docs 반영 (4개 파일)
- `README.md`: 시나리오 1 설명에 "note-path default-directory placeholder" 추가 (response copy button state, source filename도 함께 정리)
- `docs/ACCEPTANCE_CRITERIA.md`: note-path placeholder contract에 coverage 명시 ("one focused unit test + one Playwright scenario-1 assertion")
- `docs/MILESTONES.md`: Milestone 3의 Playwright smoke suite 항목에 시나리오 1 coverage 확장 내역 반영
- `docs/TASK_BACKLOG.md`: Implemented 항목 12의 smoke coverage 설명에 동일 내역 반영

### 변경하지 않은 것
- 코드 변경 없음
- 테스트 변경 없음

## 검증
- `git diff --check` — 통과
- `make e2e-test` — docs-only 라운드이므로 생략. 이전 라운드에서 test 추가와 함께 98 unit tests OK + 12/12 E2E green 확인 완료이며, 이번 라운드는 문서 문구만 변경했으므로 `git diff --check`만으로 충분합니다.

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
