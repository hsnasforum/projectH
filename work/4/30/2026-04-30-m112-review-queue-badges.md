# 2026-04-30 M112 Review Queue 항목 배지

## 변경 파일

- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `work/4/30/2026-04-30-m112-review-queue-badges.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록과 실제 검증 결과 정리에 사용

## 변경 이유

- M110 검색 필터와 M111 항목 수 헤더 이후, Review Queue 각 후보의 우선순위 판단에 필요한 맥락 정보를 항목 내부에서 바로 볼 수 있어야 했습니다.
- 현재 handoff는 Review Queue 항목에 Age, Family, Quality 배지를 추가하는 클라이언트 전용 Axis 1 범위였습니다.

## 핵심 변경

- `ReviewQueuePanel.tsx`에 `relativeAgeLabel()` helper를 추가해 `derived_at` 기준 상대 시간을 `N분 전`, `N시간 전`, `N일 전`으로 표시합니다.
- 각 항목에 `data-testid="review-queue-item-age"` 배지를 항상 표시합니다.
- 각 항목에 `data-testid="review-queue-item-family"` 배지를 항상 표시하고 `candidate_family` 원문 값을 노출합니다.
- `quality_info?.is_high_quality === true`일 때만 `data-testid="review-queue-item-quality"` 배지와 `고품질` 레이블을 표시합니다.
- 기존 항목 상단의 `고품질` 표시는 새 Quality 배지로 옮겨 중복 표시를 피했습니다.

## 검증

- `python3 -m py_compile app/handlers/reviewed_memory.py` — PASS
- `rg -n "review-queue-item-age|review-queue-item-family|review-queue-item-quality" app/frontend/src/components/ReviewQueuePanel.tsx` — PASS
- `git diff --check -- app/frontend/src/components/ReviewQueuePanel.tsx` — PASS
- `git diff --name-only -- app/frontend/src/` — PASS, `app/frontend/src/components/ReviewQueuePanel.tsx`만 출력
- `cd app/frontend && npx tsc --noEmit` — PASS

## 남은 리스크

- 이번 라운드는 source-only Axis 1로 제한되어 Playwright와 dist 재빌드는 실행하지 않았습니다.
- `review-queue-item-age`, `review-queue-item-family`, `review-queue-item-quality`의 E2E smoke와 dist 반영은 별도 Axis 2가 필요합니다.
