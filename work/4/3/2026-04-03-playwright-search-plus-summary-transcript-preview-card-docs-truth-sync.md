# 2026-04-03 playwright search-plus-summary transcript preview-card docs truth-sync

**범위**: folder-search(search-plus-summary) transcript preview panel regression coverage를 root docs 4개에 반영

---

## 변경 파일

- `README.md` — scenario 3 설명에 transcript preview panel coverage 추가
- `docs/ACCEPTANCE_CRITERIA.md` — folder picker bullet에 동일 반영
- `docs/MILESTONES.md` — Playwright smoke suite parenthetical의 folder-search 설명에 동일 반영
- `docs/TASK_BACKLOG.md` — 완료 항목 12번 parenthetical의 folder-search 설명에 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 folder-search 시나리오에 transcript preview panel assertion이 landed되었지만, root docs 4개의 scenario 3 smoke coverage 설명은 아직 source-type label과 metadata까지만 적고 preview panel coverage를 누락하고 있었음.

---

## 핵심 변경

1. 4개 docs 모두 folder-search smoke 설명 끝에 "plus transcript preview panel with item count, first card filename, and match badge" 추가

---

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `rg -n "transcript preview panel" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 4개 파일 모두 반영 확인

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- document-search preview-card contract의 search-only + search-plus-summary 양쪽 code/regression/docs가 모두 정합한 상태. same-family current-risk 닫힘.
