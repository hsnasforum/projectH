# 2026-04-03 playwright preview-card tooltip docs truth-sync

**범위**: preview-card full-path tooltip regression coverage를 `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에 반영

---

## 변경 파일

- `docs/MILESTONES.md` — Milestone 3의 search-only smoke 항목에 full-path tooltip coverage 추가
- `docs/TASK_BACKLOG.md` — 완료 항목 13번에 full-path tooltip coverage 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 preview-card filename의 full-path tooltip regression coverage가 e2e 테스트에 landed되고 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`에는 반영됐지만, `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`는 아직 `selected-copy`까지만 적고 tooltip coverage를 누락하고 있었음.

---

## 핵심 변경

1. `docs/MILESTONES.md` — search-only smoke 항목 끝에 "and full-path tooltip on preview card filenames in both response detail and transcript" 추가
2. `docs/TASK_BACKLOG.md` — 항목 13번 끝에 "and full-path tooltip on preview card filenames" 추가

---

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `rg -n "selected-copy|tooltip|search-only response|preview card" docs/MILESTONES.md docs/TASK_BACKLOG.md` — 2개 파일 모두 반영 확인

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- preview-card tooltip family의 code/regression/docs(README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG)가 모두 정합한 상태. same-family current-risk 닫힘.
