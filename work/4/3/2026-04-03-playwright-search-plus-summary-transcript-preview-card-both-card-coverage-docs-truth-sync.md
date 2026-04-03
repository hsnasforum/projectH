# 2026-04-03 playwright search-plus-summary transcript preview-card both-card coverage docs truth-sync

**범위**: folder-search scenario 3의 both-card coverage를 root docs 4개에 반영

---

## 변경 파일

- `README.md` — scenario 3 설명을 "first card filename, full-path tooltip, match badge, and snippet visibility" → "both cards' filenames, full-path tooltips, match badges, and snippet visibility"로 갱신
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 반영
- `docs/MILESTONES.md` — 동일 반영
- `docs/TASK_BACKLOG.md` — 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 여러 라운드에서 folder-search 시나리오에 second card의 filename, tooltip, badge, snippet assertion이 모두 landed되었지만, root docs 4개는 아직 first-card coverage만 기술하고 있어 both-card browser truth와 어긋남.

---

## 핵심 변경

1. 4개 docs 모두 scenario 3 folder-search smoke 설명을 both-card 기준으로 갱신

---

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `rg` 4개 파일 모두 반영 확인

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- folder-search transcript preview-card both cards × all properties의 code/regression/docs 모두 정합. search-plus-summary preview-card family current-risk 닫힘.
