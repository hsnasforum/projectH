STATUS: verified
CONTROL_SEQ: 941
BASED_ON_WORK: work/4/23/2026-04-23-milestone12-axis5-preference-visibility.md
HANDOFF_SHA: fd864d6
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 937

## Claim

Milestone 12 Axis 5 — Preference Visibility:
- `scripts/audit_traces.py`: `PreferenceStore.get_candidates()` + `get_active_preferences()` 추가 → `Preferences: candidate=N, active=M` 출력
- `scripts/export_traces.py`: `PREF_PATH` 상수 + preference JSONL export 추가 (`data/preference_assets.jsonl`)
- `tests/test_export_utility.py`: `TestPreferenceExport` 클래스 2건 추가

## Checks Run

- `python3 -m py_compile scripts/audit_traces.py scripts/export_traces.py tests/test_export_utility.py` → OK
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets -v` → **51/51 통과** (기존 49 + 신규 2)
- `python3 scripts/audit_traces.py | grep "Preferences:"` → `Preferences:       candidate=23, active=0`
- `python3 scripts/export_traces.py | grep "Preference assets:"` → `Preference assets: 23 → data/preference_assets.jsonl`
- `git diff --check -- scripts/audit_traces.py scripts/export_traces.py tests/test_export_utility.py` → OK

## Code Review

### `scripts/audit_traces.py`

- `PreferenceStore` import 추가, `get_candidates()` + `get_active_preferences()` 호출. 올바름.
- summary 마지막 줄에 `Preferences: candidate=N, active=M` 추가. 올바름.
- `storage/session_store.py` / contracts 미수정. handoff 범위 준수.

### `scripts/export_traces.py`

- `PreferenceStore` import + `PREF_PATH = Path("data/preference_assets.jsonl")` 추가. 올바름.
- 기존 correction pair export 로직 무변경. 그 뒤에 preference export 루프 추가. 올바름.
- `get_candidates() + get_active_preferences()` — CANDIDATE·ACTIVE만 포함. REJECTED·PAUSED 제외. 올바름.

### `tests/test_export_utility.py` — `TestPreferenceExport` 신규 2건

- `test_preference_assets_path_targets_data_jsonl`: `PREF_PATH.name == "preference_assets.jsonl"` + `parent.name == "data"` — 경로 상수 검증. 올바름.
- `test_preference_export_includes_candidates_and_active`: 임시 PreferenceStore에 CANDIDATE 1건 + ACTIVE 1건(activate_preference 호출) 생성 → `get_candidates() + get_active_preferences()` → JSONL 출력 → preference_id 2건 + status 2종 검증. 올바름.
- `stream_trace_pairs()` feedback 확장 / `_is_high_quality` 세분화 — handoff 범위 제외 확인. 올바름.

## Milestone 12 Axes 1–5 요약

| axis | seq | SHA | 내용 |
|---|---|---|---|
| 1 | 921 | 6838aba | trace audit baseline |
| 2 | 925 | 701166b | trace export utility |
| 3 | 929+933 | f13a1ad+966fdb4 | quality scoring + threshold 재조정 |
| 4 | 935 | 215096d | asset promotion pipeline |
| 5 | 940 | (미커밋) | preference visibility |

## Risk / Open Questions

- approval/rejection 신호 0 gap 미해결 — 구현 문제가 아닌 사용 데이터 축적 문제.
- Milestone 12 close 여부: Axes 1–5로 "promote" 목표 완료, preference 가시성 확보. "evaluate model layer" 목표 및 approval trace precondition은 미충족.
- advisory 재요청 필요: Gemini가 Axis 5 이후 M12 close 허용할지 확인.
- 브라우저/Playwright 미실행: frontend 변경 없음.
