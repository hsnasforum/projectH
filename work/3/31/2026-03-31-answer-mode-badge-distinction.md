# 2026-03-31 entity-card / latest-update answer mode badge distinction

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- ACCEPTANCE_CRITERIA: "Latest-update responses should remain clearly separated from entity-card responses."
- 기존에는 answer mode가 origin detail 문자열 안에 `·` 구분자로 섞여 있어 한눈에 구분 어려웠음
- TASK_BACKLOG / MILESTONES의 current-phase investigation hardening 방향과 직결

## 핵심 변경

### UI 변경
- `formatOrigin()`: answer mode를 별도 `answerModeBadge` 필드로 반환 (detail 문자열에서 제거)
- 응답 패널 헤더에 `#response-answer-mode-badge` 요소 추가 (origin badge와 detail 사이)
- web investigation 응답(`entity_card` / `latest_update`)일 때만 표시, 일반 응답에서는 hidden
- `.answer-mode-badge` 스타일: 10px, 파란색 pill badge로 origin badge와 시각적으로 구분

### docs 반영 (3개 파일)
- `README.md`: "response origin badge with separate answer-mode badge for web investigation"
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: "The response origin area shows a separate answer-mode badge" 추가

### 변경하지 않은 것
- backend answer mode 분류 로직 변경 없음
- search ranking, source weighting 변경 없음
- transcript 메시지의 origin rendering은 기존 detail 문자열 유지 (response panel header만 변경)

## 검증
- `make e2e-test` — `12 passed (2.5m)`
- `git diff --check` — 통과

## 남은 리스크
- answer mode badge는 web investigation에서만 표시되므로 mock adapter smoke에서는 직접 검증되지 않음 (mock은 web investigation을 수행하지 않음)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
