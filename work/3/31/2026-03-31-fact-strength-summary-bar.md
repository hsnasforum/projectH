# 2026-03-31 web investigation entity-card fact-strength summary bar

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- TASK_BACKLOG "Current Phase In Progress": "Distinguish strong facts, single-source facts, and unresolved slots more clearly"
- web investigation 응답에서 fact-strength 정보가 quick-meta의 작은 텍스트와 접기 가능한 claim-coverage 패널에만 있어, 사용자가 응답을 읽기 전에 사실 검증 상태를 한눈에 파악하기 어려웠음
- 기존 claim-coverage 데이터와 `summarizeClaimCoverageCounts()`를 재활용하여 새 vocabulary 없이 구현

## 핵심 변경

### UI 변경
- `#fact-strength-bar` 요소 추가 (quick-meta와 response-text 사이)
- `renderFactStrengthBar()` 함수: claim_coverage 데이터에서 strong/weak/missing 카운트를 색상 코드 badge로 표시
  - 초록: 교차 확인 N
  - 노랑: 단일 출처 N
  - 빨강: 미확인 N
- claim_coverage가 없으면 bar hidden (일반 문서 요약에서는 표시되지 않음)
- `renderSession`과 `renderResult` 양쪽에서 호출
- empty state에서도 hidden 처리

**예시 (web investigation 응답):**
```
[응답 헤더] OLLAMA  설명 카드
[quick-meta] 출처 유형 공식 기반(높음), 보조 기사(보통) · ...
[fact-strength bar] 사실 검증: [3] 교차 확인  [2] 단일 출처  [1] 미확인
[응답 본문] ...
```

### CSS
- `.fact-strength-bar`: 라운드 패널, flex-wrap
- `.fact-count.strong/weak/missing`: 초록/노랑/빨강 pill badge

### docs 반영 (3개 파일)
- `README.md`: "color-coded fact-strength summary bar above the response text for web investigation" 추가
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: fact-strength summary bar contract 명시

### smoke limitation
- mock adapter는 web investigation을 수행하지 않으므로 fact-strength bar를 dedicated assertion으로 고정할 수 없음. 일반 문서 요약에서는 bar가 hidden이므로 기존 smoke에 영향 없음.

## 검증
- `make e2e-test` — `12 passed (2.7m)`
- `git diff --check` (이번 변경 파일만) — 통과
- 참고: `git diff --check` 전체에서 `.pipeline/codex_feedback.md`의 기존 trailing whitespace가 보이지만 이번 라운드 변경이 아님

## 남은 리스크
- fact-strength bar는 web investigation에서만 생성되므로 mock smoke에서 직접 검증 불가
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
