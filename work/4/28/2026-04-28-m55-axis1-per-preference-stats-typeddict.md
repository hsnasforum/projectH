# 2026-04-28 M55 Axis 1 PerPreferenceStats TypedDict

## 변경 파일

- `core/contracts.py`
- `storage/preference_utils.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m55-axis1-per-preference-stats-typeddict.md`

## 사용 skill

- `security-gate`: per-preference reliability stats는 session audit summary에서 파생되는 로컬 저장 통계 표면이므로 저장 동작 변경 여부를 확인했습니다.
- `doc-sync`: 구현된 `PerPreferenceStats` 계약을 handoff가 지정한 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M54에서 correction record 계약을 `TypedDict`로 공식화한 뒤, preference reliability 집계의 `per_preference_stats`도 최소 필드 계약을 명시할 필요가 있었습니다. 이번 slice는 `applied_count`와 `corrected_count` 타입 표면만 추가하고, 실제 session_store 집계 리터럴이나 저장 동작은 변경하지 않았습니다.

## 핵심 변경

- `core/contracts.py`에 `PerPreferenceStats(TypedDict, total=False)`를 추가했습니다.
- `PerPreferenceStats` 필드는 `applied_count: int`, `corrected_count: int` 두 개로 한정했습니다.
- `storage/preference_utils.py`에서 `PerPreferenceStats`를 import하고 `enrich_preference_reliability()`의 `per_preference_stats` 타입을 `Mapping[str, PerPreferenceStats] | None`으로 강화했습니다.
- `docs/MILESTONES.md`에 M55 Preference Stats Schema Axis 1 항목을 추가했습니다.

## 검증

- `python3 -m py_compile core/contracts.py storage/preference_utils.py`
  - 통과
- `python3 -m unittest -v tests.test_preference_handler`
  - 통과, 20개 테스트 OK
- `git diff --check -- core/contracts.py storage/preference_utils.py docs/MILESTONES.md`
  - 통과

## 남은 리스크

- `storage/session_store.py`의 `setdefault` dict 리터럴 타입 주석은 handoff 경계상 Axis 2 대상이라 변경하지 않았습니다.
- `tests/test_preference_injection.py`, `tests/test_session_store.py`, frontend, dist, E2E, approval, sqlite_store는 변경하지 않았습니다.
