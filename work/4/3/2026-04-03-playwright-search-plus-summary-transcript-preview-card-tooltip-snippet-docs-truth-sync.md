# 2026-04-03 playwright search-plus-summary transcript preview-card tooltip-snippet docs truth-sync

**범위**: folder-search scenario 3의 first-card tooltip + snippet regression coverage를 root docs 4개에 반영

---

## 변경 파일

- `README.md` — scenario 3 설명에 full-path tooltip과 snippet visibility 추가
- `docs/ACCEPTANCE_CRITERIA.md` — folder picker bullet에 동일 반영
- `docs/MILESTONES.md` — Playwright smoke suite parenthetical의 folder-search 설명에 동일 반영
- `docs/TASK_BACKLOG.md` — 완료 항목 12번 parenthetical의 folder-search 설명에 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 두 라운드에서 folder-search 시나리오에 first-card tooltip과 snippet assertion이 landed되었지만, root docs 4개는 아직 "item count, first card filename, and match badge"까지만 적고 tooltip + snippet coverage를 누락하고 있었음.

---

## 핵심 변경

1. 4개 docs 모두 folder-search scenario 3 설명의 "first card filename, and match badge" → "first card filename, full-path tooltip, match badge, and snippet visibility"로 갱신

---

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `rg` 4개 파일 모두 반영 확인

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- folder-search first card의 filename/tooltip/badge/snippet이 code/regression/docs 모두 정합. second card는 별도 슬라이스 대상.
