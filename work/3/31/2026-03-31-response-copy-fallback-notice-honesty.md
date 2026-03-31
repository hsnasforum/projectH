# 2026-03-31 response copy fallback notice honesty

## 변경 파일
- `app/templates/index.html`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- `navigator.clipboard` 미지원 환경의 fallback path에서 `document.execCommand("copy")` 반환값을 확인하지 않아, 복사 실패 시에도 성공 notice를 띄우는 honesty risk

## 핵심 변경

### code 변경
- `copyTextValue()` fallback branch: `execCommand("copy")` 반환값(`boolean`)을 확인
  - `true`: 기존대로 success notice 표시
  - `false`: "클립보드 복사에 실패했습니다. 텍스트를 직접 선택해 복사해 주세요." failure notice 표시

### docs 반영
- `docs/ACCEPTANCE_CRITERIA.md`: fallback failure notice honesty contract 명시

### 변경하지 않은 것
- `navigator.clipboard.writeText` success path (변경 없음, 이미 smoke로 검증됨)
- 버튼 존재/gating 로직 (변경 없음)
- `README.md`, `docs/PRODUCT_SPEC.md` (fallback은 구현 세부사항이므로 root docs 변경 불필요)

## 검증
- `make e2e-test` — `12 passed (2.7m)`
- `git diff --check` — 통과

## 남은 리스크
- fallback failure branch는 `navigator.clipboard`가 없는 구형 브라우저에서만 실행되므로 Playwright headless(Chromium)에서는 직접 검증 불가. 이 사실은 정직하게 인정하며, 코드 리뷰로만 확인 가능합니다.
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
