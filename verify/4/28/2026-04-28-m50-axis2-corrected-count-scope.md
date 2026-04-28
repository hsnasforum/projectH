STATUS: verified
CONTROL_SEQ: 1167
BASED_ON_WORK: work/4/28/2026-04-28-m50-axis2-corrected-count-scope.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1167
VERIFIED_BY: Claude
NEXT_CONTROL: advisory_request.md CONTROL_SEQ 1168

---

# 2026-04-28 M50 Axis 2 — corrected_count 집계 범위 확장 검증

## 이번 라운드 범위

백엔드 집계 + 단위 테스트 + milestone 문서 —
`storage/session_store.py`, `tests/test_session_store.py`, `docs/MILESTONES.md`.

approval, preference lifecycle, frontend, dist 변경 없음.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile storage/session_store.py tests/test_session_store.py` | **PASS** |
| `python3 -m unittest -v tests.test_session_store` | **18 tests OK** |
| `git diff --check` (3개 파일) | **PASS** (exit 0) |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `session_store.py:1027` — `is_personalized_correction = msg.get("corrected_text") is not None` (`grounded_brief` 조건 제거) | ✓ |
| `session_store.py:733–736` — `is_applied_preference_response` 변수 추가 | ✓ |
| `session_store.py:746` — `_normalize_message()`가 `is_grounded_brief_source or is_applied_preference_response`일 때 `corrected_text` 보존 | ✓ |
| `tests/test_session_store.py:367` — `test_corrected_count_includes_non_grounded_brief_corrections` 신규 테스트 추가 | ✓ |
| 신규 테스트: chat 2건 중 corrected_text 있는 1건만 corrected_count 반영 | ✓ (18 tests OK) |
| 기존 `test_get_global_audit_summary_per_preference_stats` 회귀 없음 (grounded_brief 케이스 유지) | ✓ |
| `docs/MILESTONES.md` line 1111–1114 M50 Axis 2 ACTIVE 항목 | ✓ |
| `preference_store.py` / handlers / frontend 미수정 | ✓ |
| approval / storage boundary 미수정 | ✓ |
| commit / push / PR 미실행 | ✓ |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `storage/session_store.py` | 수정됨, 미커밋 | M50 Axis 2 |
| `tests/test_session_store.py` | 수정됨, 미커밋 | M50 Axis 2 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M50 Axis 2 누적 |

현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (PR #49)
HEAD: `5997257` (M50 Axis 1+2 commit)

## 다음 행동

M50 Axis 2 (corrected_count 범위 확장) 검증 완료.
3개 파일 미커밋 — 현재 브랜치 PR #49에 추가 커밋으로 발행 후 방향 어드바이저리.
→ `advisory_request.md` CONTROL_SEQ 1168 — M50 다음 슬라이스 방향 결정 (명시적 피드백 UI vs M51).
