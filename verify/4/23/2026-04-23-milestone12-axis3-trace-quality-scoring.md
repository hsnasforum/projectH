STATUS: verified
CONTROL_SEQ: 970
BASED_ON_WORK: work/4/23/2026-04-23-milestone13-axis4-per-preference-reliability.md
HANDOFF_SHA: 1c80563
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 966

## Claim

Milestone 13 Axis 4 — Per-Preference Reliability Analysis:
- `storage/session_store.py`: `get_global_audit_summary()`에 `per_preference_stats` 맵 추가; 기존 Axis 3 블록을 `is_personalized_correction` 변수로 리팩터; `for pref_id in msg["applied_preference_ids"]:` 루프로 fingerprint별 `applied_count` / `corrected_count` 누적
- `scripts/audit_traces.py`: per-preference correction rate를 correction rate 내림차순 정렬 출력; per_preference_stats가 없으면 N/A 출력
- `tests/test_session_store.py`: `test_get_global_audit_summary_per_preference_stats` 1건 추가 (pref-A 2회 적용 1회 correction, pref-B 1회 적용 1회 correction 검증)

## Checks Run

- `python3 -m py_compile storage/session_store.py scripts/audit_traces.py` → OK (exit 0)
- `python3 -m unittest tests.test_session_store ... tests.test_evaluate_traces -v` → **60/60 통과** (기존 59 + 신규 1)
- `python3 scripts/audit_traces.py` → `per_preference_stats: {}`, `Per-preference reliability: N/A (no personalized responses yet)` 출력 OK
- `git diff --check -- storage/session_store.py scripts/audit_traces.py tests/test_session_store.py` → OK (exit 0)

## Actual Diff (key additions)

**`storage/session_store.py`** — 초기화 + 루프 확장:
```python
# 초기화:
"per_preference_stats": {},

# 기존 Axis 3 블록 리팩터 + 루프 추가:
if msg.get("applied_preference_ids"):
    summary["personalized_response_count"] += 1
    is_personalized_correction = (
        str(msg.get("artifact_kind") or "") == "grounded_brief"
        and msg.get("corrected_text") is not None
    )
    if is_personalized_correction:
        summary["personalized_correction_count"] += 1
    for pref_id in msg["applied_preference_ids"]:
        pstats = summary["per_preference_stats"].setdefault(
            pref_id, {"applied_count": 0, "corrected_count": 0}
        )
        pstats["applied_count"] += 1
        if is_personalized_correction:
            pstats["corrected_count"] += 1
```

**`scripts/audit_traces.py`** — per-preference 출력 (20줄):
```python
per_pref = summary.get("per_preference_stats", {})
if per_pref:
    sorted_prefs = sorted(per_pref.items(),
        key=lambda x: x[1]["corrected_count"] / x[1]["applied_count"]
        if x[1]["applied_count"] > 0 else 0, reverse=True)
    ...
else:
    print("\nPer-preference reliability: N/A (no personalized responses yet)")
```

## Code Review

- `is_personalized_correction` 추출: 기존 Axis 3의 인라인 조건을 named bool로 리팩터, 루프에서 재사용 — 중복 평가 제거. 올바름.
- `setdefault` 패턴: fingerprint 첫 등장 시 자동 초기화, 이후 누적 — idiomatic. 올바름.
- 정렬 람다의 0 나누기 방지: `if x[1]["applied_count"] > 0 else 0` — 현재 empty이므로 분기 항상 N/A. 올바름.
- `preference_store.py`, `agent_loop.py`, `correction_store.py`, 계약 파일 미수정. handoff 범위 준수.

## Milestone 13 현황

| 항목 | 상태 |
|---|---|
| preference injection (agent_loop + ollama) | ✓ 기존 구현 완료 |
| Axis 1: applied_preference_ids session 저장 + export | ✓ 8cea2f1 |
| Axis 2: correction record preference link | ✓ a4f4cbd |
| Axis 3: global effectiveness metric baseline | ✓ 399122f |
| Axis 4: per-preference reliability analysis | ✓ 이번 (미커밋) |
| MILESTONES.md Axes 1–4 기록 | Axis 4 미반영 (commit 후 doc-sync 예정) |
| preference CANDIDATE → ACTIVE 전환 | deferred (guard rail) |
| PR #27 (feat/watcher-turn-state → main) | Draft 상태 |

## Bundle to Commit (operator_request.md CONTROL_SEQ 970)

### Commit 1 — Axis 4 코드 + 검증 산출물
- `storage/session_store.py`
- `scripts/audit_traces.py`
- `tests/test_session_store.py`
- `verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md` (CONTROL_SEQ 970)
- `work/4/23/2026-04-23-milestone13-axis4-per-preference-reliability.md`
- `work/4/23/2026-04-23-milestone13-axis3-commit-push.md`
- `report/gemini/2026-04-23-m13-axis4-per-preference-audit.md`

### Commit 2 — MILESTONES.md Axis 4 doc-sync (Commit 1 SHA 확인 후)
- `docs/MILESTONES.md`: Shipped Infrastructure 헤딩 "Axes 1–3" → "Axes 1–4", Axis 4 항목 추가

## Risk / Open Questions

- M13 Axes 1–4 완료 시 guard rail 내 bounded slice가 더 있는지 불확실 — Commit 후 advisory 또는 operator 결정 필요.
- active preferences = 0 — per_preference_stats 항상 empty. 실제 데이터는 preference 활성화 이후.
- PR #27 merge 결정은 별도 operator 승인 필요.
