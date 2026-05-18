STATUS: verified
CONTROL_SEQ: 1461
BASED_ON_WORK: work/4/30/2026-04-30-m103-preference-reliability-toggle.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1461

---

# 2026-04-30 M103 Axis 1 preference reliability toggle — verify

## 이번 라운드 범위

CONTROL_SEQ 1460 implement_handoff (m103_axis1_preference_reliability_toggle) 실행 결과.
work note 변경 범위: 8개 파일 (Python 5개 + TypeScript 2개 + test 1개).

**주의**: 핸드오프는 Python 4개 기준이었으나 실제 변경은 5개.
`storage/preference_utils.py` 추가는 reliability projection이 저장된 값을 존중하도록
하는 same-family 필요 변경이며 work note가 이를 솔직하게 기록함.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile` (Python 5개 파일) | **PASS** |
| `test_toggle_preference_reliability_flips_flag` | **PASS** |
| `test_toggle_preference_reliability_returns_404_for_unknown_id` | **PASS** |
| `git diff --check` (8개 파일) | **PASS** |
| `toggle_preference_reliability` handler 심볼 | ✓ `app/handlers/preferences.py:402` |
| `toggle-reliability` route | ✓ `app/web.py:404, 449` |
| `togglePreferenceReliability()` TypeScript 함수 | ✓ `app/frontend/src/api/client.ts:555` |
| `data-testid="toggle-reliability-btn"` UI | ✓ `PreferencePanel.tsx:715` |

Ran 2 tests in 0.087s — OK.

## M103 Axis 1 핵심 변경 요약

- `app/handlers/preferences.py`: `toggle_preference_reliability()` — enriched 값 기반 반전, `preference_reliability_toggled` task log
- `app/web.py`: `POST /api/preferences/<id>/toggle-reliability` same-origin 라우트
- `storage/preference_store.py` + `storage/sqlite/preference.py`: 최소 `update()` 추가
- `storage/preference_utils.py`: 저장된 `is_highly_reliable` 값을 reliability projection에서 우선 존중
- `app/frontend/src/api/client.ts`: `togglePreferenceReliability()` — POST 호출, 갱신된 record 반환
- `app/frontend/src/components/PreferencePanel.tsx`: `toggle-reliability-btn` + 상태 갱신

## 남은 리스크

- dist 재빌드 미실행 — Axis 2에서 처리 필요
- `toggle-reliability-btn` dist JS 포함 여부 미확인
- E2E 시나리오 미추가 — Axis 2 범위
- docs 동기화 미실행 (is_highly_reliable 명시 저장 동작 변경 포함)
- 모든 8개 파일 미커밋 상태
