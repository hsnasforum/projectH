# 2026-03-31 verification label strength tag clarity

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- web investigation의 verification_label이 history detail과 response origin에서 `공식+기사 교차 확인`, `단일 출처 참고` 같은 raw 문자열로 표시되어, 검증 강도를 즉시 파악하기 어려웠음

## 핵심 변경

### UI 변경
- `formatVerificationLabel()` 함수 추가:
  - 강(strong): `공식+기사 교차 확인`, `공식 확인 중심`, `기사 교차 확인`, `설명형 다중 출처 합의`
  - 중(medium): `공식 단일 출처`, `설명형 단일 출처`
  - 약(weak): `다중 출처 참고`, `단일 출처 참고`, 그 외
- 적용 위치:
  - web history detail line: `공식+기사 교차 확인` → `검증: 공식+기사 교차 확인 [강]`
  - response origin detail: 동일 패턴 적용

### docs 반영 (3개 파일)
- `README.md`: "verification strength tags" 추가
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: verification strength tag contract 명시

## 검증
- `make e2e-test` — `12 passed (3.1m)`
- `git diff --check` — 통과

## 남은 리스크
- verification label은 web investigation에서만 생성되므로 mock adapter smoke에서는 직접 검증 불가
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
