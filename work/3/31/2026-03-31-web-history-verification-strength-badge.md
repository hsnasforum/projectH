# 2026-03-31 web history verification-strength badge

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- web history card에서 verification strength가 detail line text에만 섞여 있어 빠른 스캔이 어려웠음
- answer-mode badge는 이미 header에 있으나, 검증 강도는 아직 badge가 아니었음

## 핵심 변경

### UI 변경
- `verificationStrengthClass()` 함수 추가: `ver-strong`/`ver-medium`/`ver-weak` CSS class 반환
- `formatVerificationBadge()` 함수 추가: `검증 강`/`검증 중`/`검증 약` compact text
- `.verification-badge` CSS 3가지 색상:
  - `.ver-strong`: 초록 (강한 교차 검증)
  - `.ver-medium`: 노랑 (단일 신뢰 출처)
  - `.ver-weak`: 빨강 (약한 참고)
- history card header에 verification-strength badge 추가 (answer-mode badge 옆)
- detail line에서 verification label 제거 (badge로 이동)

### docs 반영 (3개 파일)
- `README.md`: "color-coded verification-strength badges" 명시
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: verification-strength badge contract 명시

### smoke limitation
- mock adapter는 web investigation을 수행하지 않으므로 verification-strength badge를 dedicated assertion으로 고정할 수 없음

## 검증
- `make e2e-test` — `12 passed (3.1m)`
- `git diff --check` — 통과

## 남은 리스크
- web investigation badge들은 mock smoke에서 직접 검증 불가
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
