# streaming-cancel enabled-only pre-click gate reproducibility stabilization

날짜: 2026-04-04

## 목표

cancel test의 pre-click gate를 enabled-only로 수축하여 full-suite 재현성을 다시 안정화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 912 제거)
  - 기존: `toBeEnabled()` + `not.toHaveText("파일 요약 생성 중")` (2단계 gate)
  - 교체: `toBeEnabled()` only (1단계 gate)
  - `toBeEnabled()`가 이미 `state.currentRequestId` 설정을 보장하므로 phase-title wait�� 불필요한 추가 대기였음
  - extra wait 동안 stream이 완료될 수 있어 오히려 race window를 넓힘

## 변경하지 않은 것

- line 914의 success notice assertion (유지)
- runtime cancel 로직
- verdict-state family, aggregate, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `npx playwright test -g '스트리밍 중 취소 버튼이 동작합니다' --repeat-each=3`: **3 passed (21.0s)**
- `make e2e-test`: **17 passed (4.1m)**

## python3 -m unittest 생략 사유

test-only 변경이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.
