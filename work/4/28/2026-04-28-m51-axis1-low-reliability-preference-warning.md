# 2026-04-28 M51 Axis 1 신뢰도 저하 활성 선호 경고

## 변경 파일

- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_handler.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m51-axis1-low-reliability-preference-warning.md`

## 사용 skill

- `doc-sync`: 구현된 aggregate/UI 계약을 handoff가 지정한 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M49 이후 모델 프롬프트에는 `is_highly_reliable=True`인 ACTIVE 선호만 주입됩니다. 하지만 PreferencePanel에서는 ACTIVE 상태로 보이는 선호가 교정 비율 때문에 실제 주입 대상에서 제외될 수 있어, 사용자가 신뢰도 저하 상태를 알아보기 어렵습니다. 이번 slice는 `applied_count >= 3`이고 `is_highly_reliable is not True`인 ACTIVE 선호 개수를 backend payload와 PreferencePanel header에 노출하는 데 한정했습니다.

## 핵심 변경

- `/api/preferences` payload에 `low_reliability_active_count`를 추가했습니다.
- TypeScript `PreferencesPayload`에 `low_reliability_active_count?: number | null`을 추가했습니다.
- `PreferencePanel`에서 payload 값을 읽고, 값이 없을 때는 현재 visible preference의 `reliability_stats.applied_count >= 3` 및 `is_highly_reliable !== true` 조건으로 fallback 계산하게 했습니다.
- `lowReliabilityActiveCount > 0`이면 header aggregate line에 `data-testid="low-reliability-count"`가 붙은 `신뢰도 저하 N건` 배지를 표시합니다.
- `tests.test_preference_handler`에 산입 조건과 all-reliable zero 조건을 검증하는 단위 테스트 2개를 추가했습니다.
- `docs/MILESTONES.md`에 M51 Axis 1 범위와 dist/E2E 후속 경계를 기록했습니다.

## 검증

- `python3 -m py_compile app/handlers/preferences.py tests/test_preference_handler.py`
  - 통과
- `python3 -m unittest -v tests.test_preference_handler`
  - 통과, 20개 테스트 OK
  - 신규 `test_list_preferences_payload_counts_low_reliability_active_preferences` 통과
  - 신규 `test_list_preferences_payload_zero_low_reliability_when_all_reliable` 통과
- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
  - 통과
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_handler.py docs/MILESTONES.md`
  - 통과

## 남은 리스크

- `app/static/dist/` 재빌드는 handoff 경계상 금지되어 실행하지 않았습니다. dist 반영과 E2E는 다음 Axis 2 대상입니다.
- Playwright/E2E는 이번 slice 검증 범위가 아니라 실행하지 않았습니다.
- preference lifecycle, approval, storage, `app/web.py`, 기타 `app/handlers/` 파일은 변경하지 않았습니다.
