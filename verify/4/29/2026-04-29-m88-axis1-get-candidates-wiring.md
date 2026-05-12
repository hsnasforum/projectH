STATUS: verified
CONTROL_SEQ: 1340
BASED_ON_WORK: work/4/29/2026-04-29-m88-axis1-get-candidates-wiring.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1340

---

# 2026-04-29 M88 Axis 1 — get_candidates() wiring into list_preferences_payload() — verify

## 이번 라운드 범위

`list_preferences_payload()`에 M86 Axis 1의 `get_candidates()`를 연결.
`candidate_preferences` 키를 payload에 추가 (feature-detect + fallback 패턴).
M88 Axis 1 완료 — backend-only, no frontend/dist/E2E.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `py_compile app/handlers/preferences.py tests/test_preference_handler.py` | **PASS** |
| `python3 -m unittest -v tests.test_preference_handler` | **22 tests OK** — 신규 2건 포함 |
| `git diff --check -- app/handlers/preferences.py tests/test_preference_handler.py` | **PASS** |
| `git status --short -- app/frontend app/static/dist e2e storage` | **출력 없음** |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `getattr(preference_store, "get_candidates", None)` feature-detect | ✓ `preferences.py:196` |
| `get_candidates()` 호출 경로 | ✓ `preferences.py:197-198` |
| `status == "candidate"` 필터 fallback | ✓ `preferences.py:199-200` |
| `enrich_preference_reliability()` 적용 | ✓ `preferences.py:201-203` |
| `"candidate_preferences"` key 반환 | ✓ `preferences.py:244` |
| 기존 `candidate_count` 유지 (backward compat) | ✓ `preferences.py:234` |
| `test_list_preferences_payload_includes_candidate_preferences_with_fallback` 신규 | ✓ |
| `test_list_preferences_payload_uses_get_candidates_when_available` 신규 | ✓ `get_candidates_calls == 1` 검증 |

## Dirty Tree (브랜치: feat/m87-bundle)

| 파일 | 출처 | 상태 |
|------|------|------|
| `app/handlers/preferences.py` | M88 Axis 1 | M (uncommitted) |
| `tests/test_preference_handler.py` | M88 Axis 1 | M (uncommitted) |

storage/frontend/dist/e2e 미변경.

## 남은 리스크

- M88 Axis 1은 backend payload 변경만. `candidate_preferences` 키는 frontend가 아직 사용하지 않음 — 후속 UI wiring은 별도 라운드 대상.
- 기존 `candidate_count`는 backward compat 유지.
- 브랜치 생성은 `.git/refs` 쓰기 제한으로 수행하지 못했다. uncommitted 상태.
