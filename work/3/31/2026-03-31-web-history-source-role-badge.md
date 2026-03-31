# 2026-03-31 web history source-role trust badge

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- web history card에서 source-role trust label이 detail line text에만 남아 있어 빠른 스캔이 어려웠음
- answer-mode badge와 verification-strength badge는 이미 header에 올라갔으나 source-role만 뒤처져 있었음

## 핵심 변경

### UI 변경
- `sourceRoleTrustClass()` 함수 추가: `trust-high`/`trust-medium`/`trust-low` CSS class
- `.source-role-badge` CSS 3가지 색상 (초록/노랑/빨강, verification badge보다 작은 9px)
- history card header에 중복 제거된 source-role badge 추가 (각 role마다 개별 badge)
- detail line에서 source-role text 제거 (badge로 이동)

**history card header 현재 상태:**
```
[쿼리 텍스트] 설명 카드  검증 강  공식 기반(높음)  보조 기사(보통)
              ^^^^^^^^^^  ^^^^^^  ^^^^^^^^^^^^^^  ^^^^^^^^^^^^^
              answer-mode  verify  source-role     source-role
```

### docs 반영 (3개 파일)
- `README.md`: "color-coded source-role trust badges" 명시
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: history card badge 3종(answer-mode, verification, source-role) 한 줄로 통합 명시

### smoke limitation
- mock adapter는 web investigation을 수행하지 않으므로 source-role badge를 dedicated assertion으로 고정할 수 없음

## 검증
- `make e2e-test` — `12 passed (2.6m)`
- `git diff --check` — 통과

## 남은 리스크
- web investigation badge들은 mock smoke에서 직접 검증 불가
- history card header에 badge가 3종류까지 올라왔으므로, 많은 source role이 있을 때 줄바꿈 동작을 실제 investigation에서 확인 필요
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
