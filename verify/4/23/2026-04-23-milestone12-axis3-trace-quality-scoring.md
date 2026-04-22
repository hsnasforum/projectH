STATUS: verified
CONTROL_SEQ: 935
BASED_ON_WORK: work/4/23/2026-04-23-milestone12-axis4-promote-assets.md
HANDOFF_SHA: 966fdb4
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 933

## Claim

Milestone 12 Axis 4 — Asset Promotion:
- `scripts/promote_assets.py` 신설 — `data/high_quality_traces.jsonl` → `CorrectionStore.record_correction()` + `promote_correction()`
- `tests/test_promote_assets.py` 신설 — promotion 저장 / idempotent / missing-file guard 3건

## Checks Run

- `python3 -m py_compile scripts/promote_assets.py tests/test_promote_assets.py` → OK
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets -v` → **49/49 통과** (기존 46 + 신규 3)
- `python3 scripts/export_traces.py` → `Exported 137 / High-quality 137`
- `python3 scripts/promote_assets.py` → `Promoted 137 correction pairs → data/corrections/ (0 skipped)`
- `git diff --check -- scripts/promote_assets.py tests/test_promote_assets.py` → OK

## Code Review

### `scripts/promote_assets.py`

- `promote_from_jsonl(hq_path, store)` 헬퍼 분리 → 테스트에서 직접 호출 가능. 올바름.
- `record_correction()` → `None` 시 `skipped += 1` + `continue`. identical text 방어 올바름.
- `promote_correction(result["correction_id"])` — 이미 promoted 상태면 timestamp만 갱신(idempotent). 올바름.
- missing file guard: `if not HQ_PATH.exists(): print(...); return`. 올바름.
- `storage/correction_store.py` 및 contracts 미수정 — handoff 범위 준수.

### `tests/test_promote_assets.py` — 신규 3건

- `test_promotes_pairs_to_correction_store`: 임시 JSONL → `promote_from_jsonl` → `CorrectionStatus.PROMOTED` 확인. 올바름.
- `test_promote_idempotent`: 두 번 실행 → 레코드 1건, PROMOTED 상태 유지. 올바름.
- `test_promote_missing_file_exits_cleanly`: `pa.HQ_PATH` monkeypatch → `main()` 안내 메시지 출력 후 정상 종료. 올바름.

## Milestone 12 Axes 1–4 완료 요약

| axis | seq | SHA | 내용 |
|---|---|---|---|
| 1 | 921 | 6838aba | trace audit baseline |
| 2 | 925 | 701166b | trace export utility |
| 3 | 929+933 | f13a1ad+966fdb4 | quality scoring + threshold 재조정 |
| 4 | 934 | (미커밋) | asset promotion pipeline |

## Risk / Open Questions

- `data/corrections/`에 이미 기존 record 8000+건 존재 — 성능 이슈는 아님. promotion은 137건 정상 완료.
- feedback/preference 신호 0 gap, Axis 5+ 범위 — 미해결 유지.
- Milestone 12 MILESTONES.md 반영 미완 — doc-sync 별도 handoff 필요.
- 브라우저/Playwright 미실행: frontend 변경 없음.
