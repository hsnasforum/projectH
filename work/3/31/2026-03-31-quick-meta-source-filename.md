# 2026-03-31 quick-meta source filename display

## 변경 파일
- `app/templates/index.html`
- `docs/ACCEPTANCE_CRITERIA.md`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- copy/timestamp/latency 축에서 벗어나 summary/search clarity 축으로 이동
- 단일 문서 요약이 가장 흔한 사용 패턴인데, quick-meta에 `출처 1개`로만 표시되어 사용자가 어떤 문서 기반 응답인지 즉시 알 수 없었음
- 이전 `출처 N개` 표시보다 파일명 직접 표시가 더 정직한 사용자-facing contract

## 핵심 변경

### UI 변경
- `renderResponseSummary`: 단일 출처일 때 `출처 1개` → `출처 {filename}` (예: `출처 long-summary-fixture.md`)
- `renderTranscript` 메시지 meta: 동일 패턴 적용
- 다중 출처(2개 이상)일 때는 기존 `출처 N개` 유지
- 파일명 추출: path를 `/` 또는 `\`로 분할 후 마지막 segment

### docs 반영
- `docs/ACCEPTANCE_CRITERIA.md`: "source filename in the quick-meta bar when a single source document is used" 추가

### smoke assertion
- 시나리오 1에서 `#response-quick-meta-text`에 `long-summary-fixture.md` 포함 확인

## 검증
- `make e2e-test` — `12 passed (2.4m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
