# 2026-04-03 playwright selected-copy coverage docs truth-sync

**범위**: `selected-copy` 회귀 검증 landed 사실을 root docs 4개에 truthful하게 반영

---

## 변경 파일

- `README.md` — Playwright smoke scenario 목록에 search-only 시나리오(item 4) 추가, 후속 항목 번호 4→5 ~ 16→17로 재정렬
- `docs/ACCEPTANCE_CRITERIA.md` — pure search-only bullet에 `selected-copy` 노출/클릭/notice/clipboard coverage 추가
- `docs/MILESTONES.md` — Milestone 3에 search-only response browser smoke + `selected-copy` 회귀 항목 추가
- `docs/TASK_BACKLOG.md` — 완료 항목 13번으로 search-only `selected-copy` Playwright regression 추가, 후속 번호 재정렬

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 `selected-copy` 버튼의 e2e + HTML contract 회귀 검증이 landed되었지만, root docs 4개가 그 변화를 반영하지 않아 code/docs truth mismatch가 남아 있었음. 이번 라운드는 그 docs truth-sync만 닫음.

---

## 핵심 변경

1. `README.md` — smoke scenario 목록이 16→17개로 늘어남. 새 item 4: pure search-only response with `selected-copy` visibility/click/notice/clipboard verification.
2. `docs/ACCEPTANCE_CRITERIA.md` — Current Gates의 search-only bullet에 `selected-copy` coverage 설명 추가.
3. `docs/MILESTONES.md` — Milestone 3에 search-only smoke 항목 1줄 추가.
4. `docs/TASK_BACKLOG.md` — 완료 항목 13번 추가, 기존 13~22→14~23 재정렬.

---

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `rg -n "selected-copy|search-only" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 4개 파일 모두 반영 확인

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- `selected-copy` family의 code/regression/docs가 모두 정합한 상태. same-family current-risk 닫힘.
