# 2026-04-03 playwright search-plus-summary response-detail second-card filename docs truth-sync

**범위**: scenario 3의 response detail second-card filename coverage를 root docs 4개에 반영

---

## 변경 파일

- `README.md` — scenario 3 response detail 부분을 "both cards' filenames"로 갱신
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 반영
- `docs/MILESTONES.md` — 동일 반영
- `docs/TASK_BACKLOG.md` — 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 response detail second-card filename assertion이 landed됐지만, root docs 4개는 아직 first-card 기준만 적고 second-card filename coverage를 누락하고 있었음.

---

## 핵심 변경

1. 4개 docs 모두 "with first-card filename" → "with both cards' filenames"로 갱신

---

## 검증

- `git diff --check` — 통과
- `make e2e-test` — 미실행 (docs-only, latest verify 기준 17 passed)

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- response detail both cards' filenames + first-card tooltip/badge/snippet의 code/regression/docs 정합. second-card tooltip/badge/snippet은 별도 슬라이스 대상.
