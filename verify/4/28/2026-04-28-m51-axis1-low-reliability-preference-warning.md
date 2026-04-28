STATUS: verified
CONTROL_SEQ: 1172
BASED_ON_WORK: work/4/28/2026-04-28-m51-axis1-low-reliability-preference-warning.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1172
VERIFIED_BY: Claude
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1173

---

# 2026-04-28 M51 Axis 1 — 신뢰도 저하 활성 선호 경고 검증

## 이번 라운드 범위

backend 집계 + TypeScript 타입 + PreferencePanel UI + 단위 테스트 + 문서 —
`app/handlers/preferences.py`, `app/frontend/src/api/client.ts`,
`app/frontend/src/components/PreferencePanel.tsx`,
`tests/test_preference_handler.py`, `docs/MILESTONES.md`.

`app/static/dist/` 재빌드·Playwright 미포함 (Axis 2 대상).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile` (2개 Python 파일) | **PASS** |
| `python3 -m unittest tests.test_preference_handler` | **20 tests OK** (신규 2개 포함) |
| `tsc --noEmit` | **EXIT: 0** |
| `git diff --check` (5개 파일) | **PASS** (exit 0) |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `preferences.py:201` `low_reliability_active_count = 0` 초기화 | ✓ |
| `preferences.py:213–221` 조건: `applied_count >= 3 AND is_highly_reliable is not True` | ✓ |
| `preferences.py:241` 반환 dict에 `low_reliability_active_count` 포함 | ✓ |
| `client.ts:309` `low_reliability_active_count?: number \| null` 타입 추가 | ✓ |
| `PreferencePanel.tsx:81` `lowReliabilityActiveCount` state | ✓ |
| `PreferencePanel.tsx:118–119` payload에서 읽어 state 갱신 | ✓ |
| `PreferencePanel.tsx:278–284` `data-testid="low-reliability-count"` 배지 (`신뢰도 저하 N건`) | ✓ |
| `test_preference_handler.py:318` `test_list_preferences_payload_counts_low_reliability_active_preferences` | ✓ |
| `test_preference_handler.py:364` `test_list_preferences_payload_zero_low_reliability_when_all_reliable` | ✓ |
| `docs/MILESTONES.md:1120–1125` M51 Axis 1 ACTIVE 항목 | ✓ |
| `applied_count < 3` 조건 미달 선호는 카운트 제외 | ✓ (조건 `lr_applied >= 3` 명시) |
| storage / approval / app/web.py 미수정 | ✓ |
| dist 재빌드 미실행 | ✓ (handoff 경계 준수) |
| commit / push / PR 미실행 | ✓ |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `app/handlers/preferences.py` | 수정됨, 미커밋 | M51 Axis 1 |
| `app/frontend/src/api/client.ts` | 수정됨, 미커밋 | M51 Axis 1 |
| `app/frontend/src/components/PreferencePanel.tsx` | 수정됨, 미커밋 | M51 Axis 1 |
| `tests/test_preference_handler.py` | 수정됨, 미커밋 | M51 Axis 1 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M51 Axis 1 누적 |

현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (PR #49)
HEAD: `3285333` (M50 Axis 3b)

## 다음 행동

M51 Axis 1 검증 완료. 5개 파일 커밋+푸시 후 dist 재빌드 + Playwright 격리 시나리오(Axis 2).
→ `implement_handoff.md` CONTROL_SEQ 1173 — M51 Axis 2 dist 재빌드 + E2E.
