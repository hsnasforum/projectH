STATUS: verified
CONTROL_SEQ: 17
BASED_ON_WORK: work/4/23/2026-04-23-milestone13-axis5b-preference-panel.md
HANDOFF_SHA: pending-commit
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 16

## Claim (M13 Axis 5b — PreferencePanel reliability stats display)

`app/frontend/src/api/client.ts`:
- `PreferenceRecord` 타입에 optional `reliability_stats?: { applied_count: number; corrected_count: number } | null` 추가

`app/frontend/src/components/PreferencePanel.tsx`:
- `preferenceReliabilityCounts()` helper: missing/null/non-finite count를 0으로 처리
- 각 preference card 설명 아래 `적용 N회 · 교정 M회` muted 라벨 추가
- 기존 status, description, delta summary, action 흐름 유지
- backend 파일 미수정

## Checks Run

- `cd app/frontend && ./node_modules/.bin/tsc --noEmit` → **OK**
- `git diff --check -- app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx` → OK

## Checks Not Run

- Playwright E2E / 브라우저 시각 확인 — CLAUDE.md 기준 UI 변경 시 브라우저 검증 권장이지만 이번 handoff acceptance가 `tsc --noEmit` 중심. 별도 smoke 라운드 또는 다음 E2E 실행 시 커버 필요.

## 추가 발견 (work note 누락)

`controller/js/cozy.js` (+37 lines) + `controller/js/state.js` (+11 lines) — work note 미포함, CONTROL_SEQ 16 범위 밖. 다음 슬라이스(CONTROL_SEQ 17 implement_handoff)에서 문서화 예정.

## 이전 라운드 요약

- seq 15 (ccef85a): runtime PR merge recovery routing (358/358 tests)
- seq 12–13 (8226cd7, ca6333f): parser gate scope + GUI automation-health (PR #29 merged)

## 현재 브랜치 상태 (커밋 전)

- HEAD: `ccef85a` (seq 15, main 대비 1 커밋 ahead)
- **미커밋 (Axis 5b)**: `app/frontend/src/api/client.ts`, `app/frontend/src/components/PreferencePanel.tsx`, `work/4/23/2026-04-23-milestone13-axis5b-preference-panel.md`
- **미커밋 (별도)**: `controller/js/cozy.js`, `controller/js/state.js` — CONTROL_SEQ 17 impl handoff 대상

## Risk / Open Questions

1. **Axis 5b 미커밋**: 이번 verify 라운드에서 커밋 예정.
2. **controller JS**: CONTROL_SEQ 17 implement_handoff → doc closeout 후 커밋.
3. **PR 생성**: controller JS 포함 후 일괄 PR 생성 예정.
4. **`latest_verify` artifact**: 계속 deferred.
