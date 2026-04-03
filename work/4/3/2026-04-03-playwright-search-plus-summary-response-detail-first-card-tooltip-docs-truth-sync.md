# 2026-04-03 playwright search-plus-summary response-detail first-card tooltip docs truth-sync

**범위**: scenario 3의 response detail first-card tooltip coverage를 root docs 4개에 반영

---

## 변경 파일

- `README.md` — scenario 3 response detail 부분에 "and full-path tooltip" 추가
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 반영
- `docs/MILESTONES.md` — 동일 반영
- `docs/TASK_BACKLOG.md` — 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 folder-search response detail first-card tooltip assertion이 landed됐지만, root docs 4개는 아직 "with first-card filename"만 적고 tooltip coverage를 누락하고 있었음.

---

## 핵심 변경

1. 4개 docs 모두 "with first-card filename" → "with first-card filename and full-path tooltip"으로 갱신

---

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `rg` 4개 파일 모두 반영 확인
- `make e2e-test` — 미실행 (docs-only, latest verify 기준 17 passed)

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- response detail first-card filename/tooltip의 code/regression/docs 정합. badge/snippet 및 second card는 별도 슬라이스 대상.
