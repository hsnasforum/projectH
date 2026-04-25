STATUS: verified
CONTROL_SEQ: 180
BASED_ON_WORK: work/4/25/2026-04-25-m35-applied-preference-badge-popover-failed.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 180 (E2E badge locator scope fix)

---

## M35 Axis 1: applied preference badge interactive (popover + pause) — E2E 실패

### Verdict

PARTIAL PASS / E2E 수정 필요. `MessageBubble.tsx` 구현(popover button, `data-testid`, 외부 클릭 닫기)과 frontend build는 정상. E2E 시나리오는 로케이터 범위 오류로 실패.

### Checks Run

- `node --check e2e/tests/web-smoke.spec.mjs` → OK
- `npx vite build` → `✓ built in 1.51s` (work 노트 기술 일치)
- `cd e2e && npx playwright test -g "badge 클릭" --reporter=line` → **1 failed** (12175번 줄 `toBeVisible()`)
- error-context.md 분석 → 팝오버가 열렸으나 **이전 테스트 세션의 선호**(`"reviewed-memory loop accepted preference pw-..."`)를 표시

### Root Cause

```
page.getByTestId("applied-preferences-badge").first()
```

`page.goto("/app-preview")` 후 이전 테스트가 활성화했던 세션의 메시지가 sidebar 또는 main 영역에 로드됨. 해당 메시지에도 badge가 존재하여, `page.getByTestId()` (page 전체 범위)가 현재 테스트의 새 메시지가 아닌 **이전 세션의 badge를 클릭**함.

결과: popover에는 이전 테스트의 `preferenceStatement`("reviewed-memory loop accepted preference...")가 표시되어 새 테스트의 `preferenceStatement`("reviewed-memory badge pause accepted preference...")가 일치하지 않아 `toBeVisible()` 실패.

### Implementation Review

`MessageBubble.tsx` 변경 사항은 의도대로 구현됨:
- badge: `<button data-testid="applied-preferences-badge" ... onClick={toggle}>선호 N건 반영</button>`
- popover: `<div data-testid="applied-preferences-popover">` — 선호 목록 + `data-testid="preference-pause-btn"` 버튼
- 외부 클릭 닫기: `prefBadgeRef` + `useEffect`로 구현됨
- `pauseAppliedPreference(pref.fingerprint)` → fingerprint로 preference_id를 조회 후 `pausePreference()` 호출

### Fix Required

`e2e/tests/web-smoke.spec.mjs`에서 badge/popover 로케이터를 `page.locator("main")` 범위로 제한:

```javascript
// 현재 (잘못된 범위)
const badge = page.getByTestId("applied-preferences-badge").first();
const popover = page.getByTestId("applied-preferences-popover");

// 수정 (main으로 범위 제한)
const badge = page.locator("main").getByTestId("applied-preferences-badge").first();
const popover = page.locator("main").getByTestId("applied-preferences-popover");
```

이 수정으로 현재 테스트의 새 채팅 응답에 있는 badge만 클릭하게 됨.
