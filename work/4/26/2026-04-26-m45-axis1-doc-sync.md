# 2026-04-26 M45 Axis 1 doc sync

## 변경 파일
- `docs/MILESTONES.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/26/2026-04-26-m45-axis1-doc-sync.md`

## 사용 skill
- `doc-sync`: 이미 구현된 M45 Axis 1 동작을 현재 제품/수용 기준 문서에 맞춰 반영했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- 직전 구현 라운드에서 preference reliability aggregate header와 active-only payload totals가 shipped 되었지만, milestone/product/acceptance 문서에는 아직 M45 Axis 1 완료 상태가 반영되지 않았다.
- 이번 handoff는 `.pipeline/implement_handoff.md` SHA `4f0ae565a3a5d212366471fe375ad3ad0e9f119d089d9a3b3a6b5e702b7916bb` 기준 docs-only closure로 제한했다.

## 핵심 변경
- `docs/MILESTONES.md`에 Milestone 45 section을 추가하고 M45 Axis 1 shipped facts, guardrails, 검증 결과를 기록했다.
- `docs/MILESTONES.md`의 `Next 3 Implementation Priorities` item 2를 M45 Axis 1 shipped 상태로 갱신했다.
- `docs/PRODUCT_SPEC.md`에 `/api/preferences` payload의 active-only `total_applied` / `total_corrected` aggregate와 `PreferencePanel` header 표시 조건을 current shipped behavior로 반영했다.
- `docs/ACCEPTANCE_CRITERIA.md`에 aggregate fields, active preference가 없을 때 zero totals, header 표시 조건, per-card reliability stats 유지 조건을 추가했다.
- 코드, 테스트, runtime/controller, pipeline control slot은 변경하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `4f0ae565a3a5d212366471fe375ad3ad0e9f119d089d9a3b3a6b5e702b7916bb`.
- `rg -n "Milestone 45|M45 Axis 1|total_applied|total_corrected|총 적용|Next 3 Implementation Priorities" docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`로 반영 위치 확인.
- `git diff --check -- docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` 통과.

## 남은 리스크
- docs-only handoff라 Python unit, TypeScript, browser smoke는 재실행하지 않았다. 직전 구현 closeout의 handler/unit/TSC 검증 결과를 문서화한 것이며 새 런타임 동작을 추가하지 않았다.
- 작업 전부터 존재한 다른 `/work` untracked notes와 runtime/controller dirty state는 이번 handoff 범위 밖이라 건드리지 않았다.
