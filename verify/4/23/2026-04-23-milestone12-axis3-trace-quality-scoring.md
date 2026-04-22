STATUS: verified
CONTROL_SEQ: 929
BASED_ON_WORK: work/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md
HANDOFF_SHA: 701166b
VERIFIED_BY: Claude

## Claim

Milestone 12 Axis 3 — Trace Quality Scoring & Refinement:
- `scripts/export_traces.py` 전면 교체 — `compute_correction_delta` + `_is_high_quality` + 두 출력 파일
- `tests/test_export_utility.py`에 quality-scoring 테스트 4건 추가

## Checks Run

- `python3 -m py_compile scripts/export_traces.py tests/test_export_utility.py` → OK
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility -v` → **45/45 통과** (기존 41 + 신규 4)
- `git diff --check -- scripts/export_traces.py tests/test_export_utility.py` → OK
- `python3 scripts/export_traces.py`:
  - `Exported 137 correction pairs → data/all_traces.jsonl`
  - `High-quality pairs: 0 → data/high_quality_traces.jsonl`
- `wc -l data/all_traces.jsonl data/high_quality_traces.jsonl` → 137 / 0

## ⚠️ 중요 소견 — similarity_score 분포

로컬 데이터의 실제 분포 분석:

| 구간 | 건수 |
|---|---|
| `< 0.20` | **137** (전체) |
| `0.20–0.98` (high-quality) | **0** |
| `> 0.98` | 0 |

- Min: 0.0674, Max: 0.0897, Median: 0.0766
- **결론**: 현재 correction pair는 전부 grounded-brief 문서 수준 rewrite — `difflib.ratio()` 기준 similarity가 구조적으로 낮음. 필터 기준 `[0.20, 0.98]`은 문장 단위 교정에서 도출된 값이며, 문서 단위 rewrite에는 맞지 않음.

## Code Review

### `scripts/export_traces.py`

- `_is_high_quality(score)` 헬퍼 분리 → 테스트에서 직접 import 가능. 올바름.
- `compute_correction_delta` → `None` 시 `continue` (identical text skip). 올바름.
- 두 파일 동시 open + 조건부 write. 올바름.
- `delta.rewrite_dimensions.get("change_types", [])` — key 누락 방어. 올바름.
- **note**: spec 기준 구현 정확. high-quality 0건은 코드 버그가 아닌 데이터 분포 문제.

### `tests/test_export_utility.py` — 신규 4건

- `test_quality_score_in_range_is_high_quality`: moderate rewrite → is_high_quality True. 올바름.
- `test_trivial_fix_not_high_quality`: 200자 문자열 1자 변경 → score > 0.98 → False. 올바름.
- `test_complete_rewrite_not_high_quality`: "aaa…" → "bbb…" → score ≈ 0 → False. 올바름.
- `test_identical_texts_returns_none_delta`: identical → `compute_correction_delta` returns None. 올바름.

## Risk / Open Questions

- **threshold 재조정 필요**: `[0.20, 0.98]`은 현재 데이터에 맞지 않음. grounded-brief 교정의 실제 분포 (0.067–0.090)에 맞는 기준이 필요 — advisory 필요.
- 대안 품질 신호: 길이 비율, anchor artifact_id 유효성, change_types 다양성 등.
- feedback 신호 0 gap 여전히 미해결.
- 브라우저/Playwright 미실행: frontend 변경 없음.
