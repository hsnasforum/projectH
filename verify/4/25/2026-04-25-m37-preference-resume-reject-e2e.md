STATUS: partial
CONTROL_SEQ: 212
BASED_ON_WORK: work/4/25/2026-04-25-m37-preference-resume-reject-e2e.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 213 (scenario 147/148 count-agnostic fix)

---

## M37 Axis 2: preference resume/reject E2E

### Verdict

PARTIAL. 시나리오 149(resume/reject lifecycle)는 추가됐고 단독 및 전체 실행에서 통과했다. 시나리오 147 하드코딩 단언 수정과 시나리오 148 cap 문제는 미처리됐다.

- 시나리오 149: **PASS** (개별 `1 passed`, 전체 실행 내 통과)
- 시나리오 147: **FAIL** — 하드코딩 `"선호 1건 반영"` 미수정; 실제 DOM: `"[모의 응답, 선호 10건 반영]"`
- 시나리오 148: **FAIL** — `badgeCountBefore = 10`이지만 두 번째 메시지도 `선호 10건 반영`; test preference가 11번째로 cap(10) 초과되어 visible count 바깥에 위치 → pause해도 표시된 count 불변
- 전체 E2E gate: `147 passed, 2 failed`

### Checks Run

- `sed -n '12060,12070p' e2e/tests/web-smoke.spec.mjs` → 하드코딩 `"선호 1건 반영"` lines 12063-12064 여전히 존재 확인
- `cd e2e && npx playwright test ... -g "sync 후 활성화" --reporter=line` → `1 failed`
  - error-context.md: `"[모의 응답, 선호 10건 반영]"` — 누적 active prefs 10개, 단언 `"선호 1건 반영"` 불일치
- `cd e2e && npx playwright test ... -g "badge 클릭 시 popover" --reporter=line` → `1 failed`
  - error-context.md: 첫/두번째 메시지 모두 `선호 10건 반영` — test preference가 11번째, cap 초과로 표시 외; pause 후에도 count 불변

### Root Cause

**Scenario 147**: implement owner가 SEQ 207 handoff(수정 금지) 기준으로 작업했고 SEQ 212(수정 필요) 범위를 미반영. 하드코딩 단언 2줄이 그대로 남음.

**Scenario 148**: 누적 active preferences가 cap(10)을 채우면 test의 새 preference(11번째)가 `serialize_session` applied_preferences 목록 밖으로 밀려나고 mock AI가 10건을 그대로 반환. pause해도 visible count 변화 없음. 149와 동일한 pre-test playwright prefs cleanup이 필요.

### What Was Not Checked

- 전체 E2E gate green: 위 2개 실패 미해결 상태

### Next

시나리오 147 하드코딩 수정 + 시나리오 148 pre-test cleanup 추가 → `make e2e-test` 149 passed.
