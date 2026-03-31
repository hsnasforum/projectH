# 2026-03-31 response origin source-role wording clarity

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- response origin detail에 `출처 공식 기반, 보조 기사`처럼 raw source role 문자열이 나열되어 신뢰도 수준을 바로 파악하기 어려웠음
- claim-coverage panel에는 이미 trust level label이 있으나, response origin detail에는 아직 미적용

## 핵심 변경

### UI 변경
- `formatOrigin()`: source role 표시를 `출처 ...` → `출처 유형 ...`으로 변경하고, `formatSourceRoleCompact()` 적용
- `formatSourceRoleCompact()` 함수 추가: `공식 기반(높음)`, `보조 기사(보통)`, `보조 커뮤니티(낮음)` 등 compact trust label

**이전**: `Ollama 응답 · 출처 공식 기반, 보조 기사 · 모델 llama3`
**개선**: `Ollama 응답 · 출처 유형 공식 기반(높음), 보조 기사(보통) · 모델 llama3`

### docs 반영 (3개 파일)
- `README.md`: "and source-role trust labels in origin detail" 추가
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: response origin source-role compact trust label contract 명시

## 검증
- `make e2e-test` — `12 passed (2.6m)`
- `git diff --check` — 통과

## 남은 리스크
- source role은 web investigation에서만 생성되므로 mock adapter smoke에서는 직접 검증 불가
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
