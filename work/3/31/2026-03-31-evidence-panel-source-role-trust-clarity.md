# 2026-03-31 evidence panel source-role trust clarity

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- evidence panel의 각 근거 항목에 raw `[공식 기반]` suffix가 붙어 신뢰도를 즉시 파악하기 어려웠음
- claim-coverage panel과 response origin detail에는 이미 trust label이 적용되었으나 evidence panel만 남아 있었음

## 핵심 변경

### UI 변경
- evidence item title suffix: `[공식 기반]` → `[공식 기반(높음)]` (기존 `formatSourceRoleCompact()` 재사용)

**이전**: `1. 문서 근거 · 네이버뉴스 [보조 기사]`
**개선**: `1. 문서 근거 · 네이버뉴스 [보조 기사(보통)]`

### docs 반영 (3개 파일)
- `README.md`: "evidence / source panel with source-role trust labels on each evidence item"
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: evidence item trust label contract 명시

## 검증
- `make e2e-test` — `12 passed (2.6m)`
- `git diff --check` — 통과

## 남은 리스크
- source role은 web investigation에서만 생성되므로 mock adapter smoke에서는 직접 검증 불가
- investigation clarity 축의 presentation layer는 이제 3개 surface (claim-coverage, response origin, evidence) 모두에서 trust label이 일관되게 적용됨
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
