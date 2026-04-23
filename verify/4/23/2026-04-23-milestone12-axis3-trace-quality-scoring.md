STATUS: verified
CONTROL_SEQ: 974
BASED_ON_WORK: work/4/23/2026-04-23-milestone13-axis5-preference-reliability-api.md
HANDOFF_SHA: 4b04ee1
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 970

## Claim

Milestone 13 Axis 5 — Preference Reliability API Enrichment (백엔드 전용):
- `app/handlers/preferences.py`: `list_preferences_payload()`가 `session_store.get_global_audit_summary()` → `per_preference_stats`를 읽어 각 preference record에 `reliability_stats: {applied_count, corrected_count}` 추가
- `fingerprint` / `delta_fingerprint` 양쪽을 lookup key로 지원
- SQLiteSessionStore는 `get_global_audit_summary` 없음 → `getattr` 방어로 graceful fallback (기본값 0)
- `tests/test_web_app.py`: `test_list_preferences_payload_includes_reliability_stats` 1건 추가 — end-to-end: 2회 적용 1회 교정 → `applied_count=2, corrected_count=1` 검증

## Checks Run

- `python3 -m py_compile app/handlers/preferences.py` → OK (exit 0)
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_list_preferences_payload_includes_reliability_stats -v` → 1/1 OK
- `python3 -m unittest tests.test_session_store ... tests.test_evaluate_traces -v` → 60/60 OK (기존 테스트 회귀 없음)
- `git diff --check -- app/handlers/preferences.py tests/test_web_app.py` → OK (exit 0)

## Actual Diff (key changes)

**`app/handlers/preferences.py`** — `list_preferences_payload()` 확장:
```python
get_summary = getattr(self.session_store, "get_global_audit_summary", None)
summary = get_summary() if callable(get_summary) else {}
per_pref_stats = summary.get("per_preference_stats", {})
...
for pref in all_prefs:
    fingerprint = str(pref_copy.get("fingerprint") or pref_copy.get("delta_fingerprint") or "")
    stats = per_pref_stats.get(fingerprint, {})
    pref_copy["reliability_stats"] = {
        "applied_count": stats.get("applied_count", 0),
        "corrected_count": stats.get("corrected_count", 0),
    }
```

## Code Review

- `getattr` 방어: SQLiteSessionStore에 `get_global_audit_summary` 없음 — 실제 발생 케이스에 대한 정당한 방어. 올바름.
- `isinstance` 과잉 방어: `summary`, `per_pref_stats`, `applied_count`, `corrected_count` 모두 내부 코드 반환값인데 타입 체크 — CLAUDE.md 기준 "Trust internal code and framework guarantees" 위반 소지. 기능 오류는 없지만 불필요한 방어임. **비블로킹 — 코드 동작에 영향 없음.**
- `delta_fingerprint` / `fingerprint` dual-key 지원: `per_preference_stats`는 `applied_preference_ids` 기반(Axis 1 저장값), preference record는 `delta_fingerprint` 보관. 양쪽 지원이 정확한 매칭을 보장. 올바름.
- 프론트엔드 미수정 ✓, `preference_store.py` 미수정 ✓, `agent_loop.py` 미수정 ✓. handoff 범위 준수.

## Milestone 13 현황

| Axis | 내용 | SHA |
|---|---|---|
| Axis 1 | applied_preference_ids session 저장 + trace export | 8cea2f1 |
| Axis 2 | correction record preference link | a4f4cbd |
| Axis 3 | global effectiveness metric baseline | 399122f |
| Axis 4 | per-preference reliability analysis | fc86577 |
| Axis 5 | preference reliability API enrichment (백엔드) | 미커밋 |
| Axis 5b (UI) | PreferencePanel.tsx reliability 표시 | deferred |
| MILESTONES.md | Axes 1-4 기록; Axis 5 추가 예정 | 4b04ee1 |

## Bundle to Commit (operator_request.md CONTROL_SEQ 974)

### 수정 파일
- `app/handlers/preferences.py`
- `tests/test_web_app.py`
- `verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md` (CONTROL_SEQ 974)

### 신규 파일 (untracked)
- `work/4/23/2026-04-23-milestone13-axis5-preference-reliability-api.md`
- `work/4/23/2026-04-23-milestone13-axis4-commit-push.md`
- `report/gemini/2026-04-23-m13-axis5-reliability-visibility-scoping.md`

### Commit 2 (same retriage) — MILESTONES.md Axis 5 doc-sync
- `docs/MILESTONES.md`: Axes 1-4 → 1-5, Axis 5 항목 추가

## Risk / Open Questions

- `isinstance` 과잉 방어 (비블로킹): 내부 코드 반환값에 대한 불필요한 타입 가드. 기능 오류 없음.
- SQLite backend: `reliability_stats` 키는 붙지만 counts 항상 0 — SQLite parity는 별도 라운드.
- Axis 5b (PreferencePanel.tsx): 브라우저 테스트 필요 — PR merge 후 별도 라운드로 defer.
- M13 Axes 1-5 완료 후 다음 결정: PR #27 merge authorization — 실제 operator 결정.
