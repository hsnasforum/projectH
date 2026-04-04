# corrected-save initial content-verdict-state exact-text + cancel stream request gate

날짜: 2026-04-05

## 목표

1. corrected-save first bridge scenario의 initial `#response-content-verdict-state` assertion 1건을 exact-text로 강화
2. cancel test의 pre-click gate를 `waitForRequest` 기반으로 변경하여 full-suite race를 근본적으로 해결

## 변경 파일

### e2e/tests/web-smoke.spec.mjs

**line 511 (verdict-state tightening)**:
- 기존: `toContainText("최신 내용 판정은 기록된 수정본입니다.")`
- 교체: `toHaveText("최신 내용 판정은 기록된 수정본입니다.")`

**line 906-915 (cancel test stabilization)**:
- 기존: `toBeEnabled()` → `click()` (enabled-state gate)
- 교체: `waitForRequest("/api/chat/stream")` → `click()` (stream-request gate)
- `waitForRequest`는 browser의 fetch 호출 직후 fire → `state.currentRequestId`가 이미 설정됨
- stream 요청이 서버에 도달한 시점이므로 cancel POST에 유효한 request ID 보장
- `click()`의 Playwright auto-wait가 enabled 확인을 내장 처리
- 이전 접근(toBeEnabled, phase-title gate)에서는 assertion 통과 후 click 처리까지의 gap에서 stream 완료 가능성이 있었음

## 변경하지 않은 것

- line 541의 corrected-save later sibling verdict-state
- line 342, 427의 accepted-as-is verdict-state (이미 exact-text)
- line 352-353, 396-397의 rejected-state timestamp-pattern
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `npx playwright test -g '스트리밍 중 취소 버튼이 동작합니다' --repeat-each=3`: **3 passed (19.6s)**
- `make e2e-test`: **17 passed (4.2m)** (2회 실행, 첫 번째에서 test #7 pre-existing ENOENT flake 1회 발생 후 재실행에서 17 passed 확인)

## python3 -m unittest 생략 사유

test-only 변경이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- test #7 (late-flip ENOENT) pre-existing flake는 별도 조사 필요
- line 541의 corrected-save later verdict-state는 아직 broad partial
