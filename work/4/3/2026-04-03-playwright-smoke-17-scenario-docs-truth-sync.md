# 2026-04-03 playwright-smoke 17-scenario docs truth-sync

**범위**: stale "16 browser scenarios"를 current "17"로 갱신하고 새 search-only smoke 설명 추가

---

## 변경 파일

- `docs/NEXT_STEPS.md` — "16 browser scenarios" → "17 browser scenarios", search-only preview-card contract 언급 추가
- `docs/ACCEPTANCE_CRITERIA.md` — "16 core browser scenarios" → "17 core browser scenarios", search-only smoke 항목 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-only hidden-body browser regression smoke가 추가되어 current suite가 17개가 됐지만, `docs/NEXT_STEPS.md`와 `docs/ACCEPTANCE_CRITERIA.md`는 아직 16개 기준이었음. 새 quality axis로 넘어가기 전에 docs truth-sync를 먼저 닫아야 함.

---

## 핵심 변경

1. `docs/NEXT_STEPS.md:16` — count 갱신 + "pure search-only hidden-body and preview-card contract with copy-button gating" 언급 삽입.
2. `docs/ACCEPTANCE_CRITERIA.md:1315` — count 갱신 + 시나리오 목록에 search-only smoke 항목 1줄 추가.

---

## 검증

- `git diff --check -- docs/NEXT_STEPS.md docs/ACCEPTANCE_CRITERIA.md` — 통과
- `rg -n "16 browser|16 core browser|Playwright.*16" docs/*.md` — 0 matches (stale 완전 제거)
- `rg -n "17 browser|17 core browser" docs/*.md` — 2 matches (NEXT_STEPS.md, ACCEPTANCE_CRITERIA.md)
- MILESTONES.md, TASK_BACKLOG.md, README.md에는 stale count 없어 수정 불필요

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- search-only UI cleanup family (transcript body-hiding, response-box preview, copy gating, docs sync) 전체가 이번 라운드로 닫힌 상태
- 다음 슬라이스는 새 quality axis로 넘어갈 수 있음
