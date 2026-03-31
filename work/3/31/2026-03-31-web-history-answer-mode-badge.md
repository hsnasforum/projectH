# 2026-03-31 web history answer-mode badge parity

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- response origin area에는 answer-mode badge(`설명 카드`/`최신 확인`)가 이미 있으나, web history card에서는 flat text detail line 첫 항목에 섞여 있어 빠른 스캔이 어려웠음

## 핵심 변경

### UI 변경
- web history card header에 `.answer-mode-badge` 요소 추가 (investigation 응답일 때만 표시)
- detail line에서 answer mode label 제거 (badge로 이동, 중복 방지)
- non-investigation 응답은 기존대로 detail line에 "일반 검색" 유지
- 기존 `.answer-mode-badge` CSS 재사용

### docs 반영 (3개 파일)
- `README.md`: "answer-mode badges" 추가
- `docs/PRODUCT_SPEC.md`: "answer-mode badges" 추가
- `docs/ACCEPTANCE_CRITERIA.md`: history card answer-mode badge contract 명시

### smoke limitation
- current smoke는 mock adapter를 사용하여 web investigation payload를 생성하지 않으므로, history card answer-mode badge를 dedicated assertion으로 고정할 수 없음

## 검증
- `make e2e-test` — `12 passed (2.8m)`
- `git diff --check` — 통과

## 남은 리스크
- web investigation history badge는 mock smoke에서 직접 검증 불가
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
