STATUS: verified
CONTROL_SEQ: 1292
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1291
BASED_ON_WORK: work/4/29/2026-04-29-m81-promote-pattern-auto-activate.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1292

---

# 2026-04-29 M81 Axis 1 — promote_correction_pattern auto-activate

## 이번 라운드 범위

단일 파일: `app/handlers/corrections.py` 변경.
테스트 파일 미수정 (CONTROL_SEQ 1291 경계 준수).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile app/handlers/corrections.py` | **PASS** |
| `python3 -m unittest tests.test_smoke` | **PASS — 150 tests** |
| `git diff --check -- app/handlers/corrections.py` | **PASS** |

## 구현 확인

| 항목 | 위치 | 확인 결과 |
|------|------|---------|
| `PreferenceStatus` import 추가 | `corrections.py:7` | ✓ `from core.contracts import CandidateFamily, PreferenceStatus` |
| `pref =` 반환값 캡처 | `corrections.py:111` | ✓ |
| CANDIDATE → `activate_preference` 호출 | `corrections.py:129–130` | ✓ `if pref and pref.get("status") == PreferenceStatus.CANDIDATE` |
| commit / push 미실행 | HEAD: c86588e | ✓ |

## 동작 계약

- `promote_correction_pattern` 호출 시 resulting PreferenceRecord가 CANDIDATE → **즉시 ACTIVE로 전환**
- 이미 ACTIVE/PAUSED/REJECTED인 경우: `activate_preference`가 None 반환 (no-op) — 안전
- 기존 cross-session `promote_from_corrections` 자동 승격 경로 변경 없음

## 다음 행동

M81 완료 (Axis 2 없음). 1개 파일 커밋 + 스택 브랜치 push + PR 생성.
→ `operator_request.md` CONTROL_SEQ 1292.
