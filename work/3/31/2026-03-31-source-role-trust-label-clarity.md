# 2026-03-31 source role trust level label clarity

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- MILESTONES "Milestone 4": source role labeling
- TASK_BACKLOG: "Distinguish strong facts, single-source facts, and unresolved slots more clearly"
- claim-coverage에서 source role이 meta line에 `대표 출처: 공식 기반`으로 섞여 표시되어 신뢰도 수준을 직관적으로 파악하기 어려웠음

## 핵심 변경

### UI 변경 (claim coverage panel)
- source role을 meta line에서 분리하여 전용 라인으로 승격: `출처 유형: 공식 기반 (신뢰도 높음)`
- `formatSourceRoleWithTrust()` 함수 추가:
  - 높음: `공식 기반`, `백과 기반`, `데이터 기반`
  - 보통: `보조 기사`, `설명형 출처`
  - 낮음: `보조 커뮤니티`, `보조 출처`

**예시:**
```
1. [교차 확인] 출생일
   값: 1990년 3월 15일
   출처 유형: 공식 기반 (신뢰도 높음)
   근거 2건
2. [단일 출처] 소속
   값: A 대학교
   → 1개 출처만 확인됨. 교차 검증이 권장됩니다.
   출처 유형: 보조 기사 (신뢰도 보통)
   근거 1건
```

### docs 반영 (3개 파일)
- `README.md`: claim coverage panel 항목에 "source role with trust level labels" 추가
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: source role trust level contract 명시

### 변경하지 않은 것
- backend source role 산출 로직 변경 없음
- search ranking, source weighting, reinvestigation 변경 없음
- response origin detail의 `출처 ...` 문자열 변경 없음

## 검증
- `make e2e-test` — `12 passed (2.6m)`
- `git diff --check` — 통과

## 남은 리스크
- source role trust level은 web investigation에서만 생성되므로 mock adapter smoke에서는 직접 검증 불가
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
