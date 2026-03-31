# 2026-03-31 web history source-role trust clarity

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- web investigation history detail line에 `출처 공식 기반, 보조 기사`처럼 raw source-role 문자열이 남아 있었음
- claim-coverage, response origin, evidence panel에는 이미 trust label이 적용 완료

## 핵심 변경

### UI 변경
- web history detail line: `출처 공식 기반, 보조 기사` → `출처 유형 공식 기반(높음), 보조 기사(보통)`
- 기존 `formatSourceRoleCompact()` 재사용

### docs 반영 (3개 파일)
- `README.md`: "and source-role trust labels in history detail" 추가
- `docs/PRODUCT_SPEC.md`: "and source-role trust labels in history detail lines" 추가
- `docs/ACCEPTANCE_CRITERIA.md`: web history trust label contract 명시

## source-role trust label 일관성 완결

이제 4개 surface 모두에서 source-role trust label이 일관되게 적용됨:
1. **claim-coverage panel**: `출처 유형: 공식 기반 (신뢰도 높음)` (full)
2. **response origin detail**: `출처 유형 공식 기반(높음)` (compact)
3. **evidence panel**: `[공식 기반(높음)]` (bracket compact)
4. **web history detail**: `출처 유형 공식 기반(높음)` (compact)

## 검증
- `make e2e-test` — `12 passed (2.8m)`
- `git diff --check` — 통과

## 남은 리스크
- source role은 web investigation에서만 생성되므로 mock adapter smoke에서는 직접 검증 불가
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
