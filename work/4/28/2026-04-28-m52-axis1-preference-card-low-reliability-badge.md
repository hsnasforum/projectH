# 2026-04-28 M52 Axis 1 개별 카드 신뢰도 저하 배지

## 변경 파일

- `app/frontend/src/components/PreferencePanel.tsx`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m52-axis1-preference-card-low-reliability-badge.md`

## 사용 skill

- `doc-sync`: 개별 카드 배지 동작을 handoff가 지정한 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M51에서 PreferencePanel header에 `신뢰도 저하 N건` 집계 배지가 추가되었지만, 목록 안에서 어떤 ACTIVE 선호가 신뢰도 저하 상태인지 바로 식별하기 어려웠습니다. 이번 slice는 개별 preference 카드에 같은 신뢰도 저하 상태를 표시하는 데 한정했습니다.

## 핵심 변경

- `PreferencePanel` 개별 카드의 `신뢰도 높음` 배지 바로 아래에 `신뢰도 저하` 배지를 추가했습니다.
- 배지는 `pref.status === "active"`, `!isHighlyReliable`, `reliability.applied >= 3` 조건을 모두 만족할 때만 표시됩니다.
- 배지에 `data-testid="preference-low-reliability-badge"`를 추가해 다음 dist/E2E slice에서 직접 검증할 수 있게 했습니다.
- `docs/MILESTONES.md`에 M52 Axis 1 범위와 dist/E2E 후속 경계를 기록했습니다.

## 검증

- `grep -c "preference-low-reliability-badge" app/frontend/src/components/PreferencePanel.tsx`
  - `1`
- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
  - 통과
- `git diff --check -- app/frontend/src/components/PreferencePanel.tsx docs/MILESTONES.md`
  - 통과

## 남은 리스크

- `app/static/dist/` 재빌드와 Playwright/E2E는 handoff 경계상 Axis 2 대상이라 실행하지 않았습니다.
- backend, API client, storage, approval, E2E test 파일은 변경하지 않았습니다.
