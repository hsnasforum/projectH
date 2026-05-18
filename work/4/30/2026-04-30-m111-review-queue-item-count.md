# 2026-04-30 M111 Review Queue 항목 수 헤더

## 변경 파일

- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `work/4/30/2026-04-30-m111-review-queue-item-count.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록과 실제 검증 결과 정리에 사용

## 변경 이유

- M110 Review Queue 검색 필터 이후 후보 목록의 현재 로드 항목 수와 검색 필터 결과 수를 사용자가 바로 확인할 수 있어야 했습니다.
- 현재 handoff는 Review Queue 패널에 클라이언트 사이드 항목 수 헤더만 추가하는 범위였고, 백엔드 수정과 dist 재빌드는 금지되어 있었습니다.

## 핵심 변경

- `ReviewQueuePanel`의 기존 `filteredItems` 파생 결과를 재사용해 `itemCountLabel`을 추가했습니다.
- 검색어가 없거나 전체 항목이 매칭되면 `review-queue-item-count`에 `{items.length}개 항목`을 표시합니다.
- 검색어가 있고 결과가 전체보다 적으면 `{filteredItems.length} / {items.length}개 항목 (검색 결과)`를 표시합니다.
- `items.length === 0`인 경우 기존처럼 패널이 `null`을 반환하므로 카운트 헤더도 표시되지 않습니다.
- `app/frontend/src/` 변경은 `ReviewQueuePanel.tsx` 한 파일로 제한했고, dist 재빌드는 수행하지 않았습니다.

## 검증

- `python3 -m py_compile app/handlers/reviewed_memory.py` — PASS
- `git diff --check -- app/frontend/src/components/ReviewQueuePanel.tsx` — PASS
- `git diff --check -- app/frontend/src/` — PASS
- `git diff --name-only -- app/frontend/src/` — PASS, `app/frontend/src/components/ReviewQueuePanel.tsx`만 출력
- `rg -n "review-queue-item-count|itemCountLabel|개 항목" app/frontend/src/components/ReviewQueuePanel.tsx` — PASS

## 남은 리스크

- 이번 라운드는 source-only Axis 1로 제한되어 Playwright와 dist 재빌드는 실행하지 않았습니다.
- 새 `data-testid="review-queue-item-count"`에 대한 E2E smoke와 dist 반영은 별도 Axis 2가 필요합니다.
