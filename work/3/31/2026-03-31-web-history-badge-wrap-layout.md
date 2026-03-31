# 2026-03-31 web history badge wrap layout polish

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- history card header에 answer-mode + verification-strength + source-role badge가 각각 `<span>`으로 grid row에 개별 배치되어, badge 수가 많으면 세로로 길어지는 문제
- badge들이 한 줄에 나란히 보이고, 넘치면 자연스럽게 wrap되어야 빠른 스캔이 가능

## 핵심 변경

### layout 변경
- `.history-badge-row` flex wrap 컨테이너 추가 (`display: flex; flex-wrap: wrap; gap: 4px`)
- 모든 badge(answer-mode, verification-strength, source-role)를 하나의 badge-row에 수집
- badge가 하나도 없으면 badge-row 자체를 DOM에 추가하지 않음
- `.history-item-title`의 `display: grid; gap: 4px`는 유지 (title strong, badge-row, meta span이 세로로 정렬)

**이전** (grid에 badge가 각각 행):
```
[쿼리 텍스트]
설명 카드
검증 강
공식 기반(높음)
보조 기사(보통)
2026. 3. 31. 오후 2:30 · 결과 5개
```

**개선** (badge-row에 나란히):
```
[쿼리 텍스트]
설명 카드  검증 강  공식 기반(높음)  보조 기사(보통)
2026. 3. 31. 오후 2:30 · 결과 5개
```

### docs
- docs wording 변경 불필요 (이전 라운드에서 "badges in the header" 이미 반영, layout은 구현 세부사항)

### smoke limitation
- mock adapter는 web investigation을 수행하지 않으므로 badge wrap layout을 dedicated assertion으로 고정할 수 없음

## 검증
- `make e2e-test` — `12 passed (2.6m)`
- `git diff --check` — 통과

## 남은 리스크
- 실제 web investigation에서 badge 5개 이상일 때의 wrap 동작은 실제 Ollama + 웹 검색으로만 확인 가능
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
