STATUS: verified
CONTROL_SEQ: 181
BASED_ON_WORK: work/4/25/2026-04-25-m35-e2e-badge-locator-scope-fix-failed.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 181 (.last() locator fix — current message badge)

---

## M35 Axis 1: badge locator scope fix — 2차 실패

### Verdict

RECORDED + ROOT CAUSE REFINED. `main` 범위 제한 후에도 실패 지속. 더 구체적인 원인 확인: `.first()` 가 이전 테스트 세션의 badge를 선택 중.

### Root Cause (Refined)

error-context.md 분석:

```
button "선호 1건 반영" [expanded] [active] [ref=e1683]   ← 클릭된 badge
  generic "reviewed-memory loop accepted preference pw-reviewed-memory-loop-..."  ← 이전 테스트 선호
  button "일시중지"
[다음 메시지]
paragraph "[모의 응답, 선호 2건 반영] 활성화된 선호가 반영되는지 확인해 주세요."  ← 현재 테스트 응답
```

- `page.goto("/app-preview")` 후 이전 테스트(reviewed-memory loop)의 세션이 active 상태로 로드됨
- badge-pause 테스트의 새 메시지가 동일 세션에 추가됨 → 세션에 여러 badge 존재
- `page.locator("main").getByTestId("applied-preferences-badge").first()` → 세션의 **첫 번째(이전)** badge 선택
- 현재 테스트 응답 badge는 세션의 **마지막** badge

**Fix**: `.first()` → `.last()` 로 교체해 가장 최근 메시지의 badge를 선택.

현재 테스트 응답에 2개 preference (`reviewed-memory loop accepted preference...` + `reviewed-memory badge pause accepted preference...`) 가 모두 포함됨. `popover.getByText(preferenceStatement)` 는 정확히 일치하는 description을 찾을 것.

### Checks Run

- `node --check e2e/tests/web-smoke.spec.mjs` → OK (work 노트 기술 일치)
- error-context.md 분석 → `.first()` badge는 이전 세션 메시지, `.last()` badge가 현재 테스트 응답
- `main` 범위 제한은 올바름 — badge/popover는 main 내에 있음
