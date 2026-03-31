# 2026-03-31 response copy fallback notice docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 fallback notice honesty code를 수정했으나, `README.md`와 `docs/PRODUCT_SPEC.md`에 미반영, `docs/ACCEPTANCE_CRITERIA.md`의 coverage 범위 설명이 부정확하여 verify에서 `not_ready`

## 핵심 변경

### docs 반영 (3개 파일)
- `README.md`: "response copy-to-clipboard button" → "(fallback path shows failure notice when copy fails)" 추가
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: coverage 범위를 정확하게 구분 — success path는 Playwright smoke로 직접 검증, fallback failure branch는 code review only (current Chromium baseline에서 미도달)

### 변경하지 않은 것
- 코드 변경 없음
- 테스트 변경 없음

## 검증
- `git diff --check` — 통과
- `make e2e-test` — docs-only 라운드이므로 생략. 이전 라운드의 verify에서 12/12 green 확인 완료.

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
