STATUS: verified
CONTROL_SEQ: 13
BASED_ON_WORK: work/4/23/2026-04-23-pr-number-parser-gate-scope.md
HANDOFF_SHA: pending-commit
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 6

## Claim (seq 12 — PR number parser gate scope fix)

`pipeline_runtime/operator_autonomy.py`:
- `referenced_operator_pr_numbers()` — structured metadata(`PR`, `PR_URL`, `PULL_REQUEST`, `CURRENT_PR`, `GATE_PR`, `MERGE_PR`) 및 labeled current-PR line을 먼저 확인
- current gate PR field가 있으면 그 번호만 반환; 설명문의 과거 PR 번호는 gate 판정에서 제외
- current field 없을 때는 기존 full-body fallback 유지 (legacy 호환)

`tests/test_operator_request_schema.py`:
- `test_referenced_operator_pr_numbers_prefers_current_pr_field`: active `PR: .../pull/28` + 설명문 `PR #27`이 공존할 때 28만 반환 검증
- `test_referenced_operator_pr_numbers_prefers_structured_metadata`: structured `pr_url` meta가 설명문보다 우선함 검증

## Checks Run

- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/pr_merge_state.py` → OK
- `python3 -m unittest tests.test_operator_request_schema tests.test_pr_merge_state -v` → **24/24 OK** (2개 신규 포함)
- `python3 -m unittest tests.test_operator_request_schema tests.test_pr_merge_state tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v` → **357/357 OK**
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py` → OK
- `python3 -m py_compile pipeline_gui/app.py pipeline_gui/home_presenter.py tests/test_pipeline_gui_home_presenter.py` → OK (GUI, 커밋 범위 밖)
- `python3 -m unittest tests.test_pipeline_gui_home_presenter -v` → **20/20 OK** (GUI, 커밋 범위 밖 — 출처 work note 미확인)

## 이전 라운드 요약

### seq 5–6 (ba93943, 5cc7a1d, 3968fab) — 이미 main에 포함 (PR #28 merged)
- `PrMergeStatusCache`: `gh pr view` TTL 캐시, fail-closed, HEAD SHA prefix match
- `pr_merge_completed` / `pr_merge_head_mismatch` recovery 통합
- 355/355 tests (seq 6 시점)

### PR #28 merge (2026-04-23T06:39:10Z)
- mergeCommit: `58052c1d82b064d444a7e972cfe8daeebc408ba1`
- runtime: `canonical control.active_control_status=none`, `autonomy.block_reason=pr_merge_completed`

### CONTROL_SEQ 8–9 루프 근본 원인 및 해결
- `_PR_NUMBER_RE` full-body 스캔이 설명문의 과거 PR 번호까지 gate PR로 수집
- seq 12 fix: structured/labeled current-PR field 우선 파싱으로 해결
- CONTROL_SEQ 10 이후: body에 타 PR 번호 표현 제거로 workaround

## 현재 브랜치 상태

- `feat/watcher-turn-state` HEAD: `3968fab` (PR #28로 main에 병합 완료)
- **미커밋 (seq 12 범위)**: `pipeline_runtime/operator_autonomy.py`, `tests/test_operator_request_schema.py`, `work/4/23/2026-04-23-pr-number-parser-gate-scope.md`, `report/gemini/2026-04-23-pr-creation-authority-arbitration.md`
- **미커밋 (별도 범위)**: `pipeline_gui/app.py`, `pipeline_gui/home_presenter.py`, `tests/test_pipeline_gui_home_presenter.py` — 출처 work note 미확인, CONTROL_SEQ 12 범위 명시 제외

## Checks Not Run

- Playwright E2E — 이번 변경이 parser helper + unit test 전용, browser-visible contract 미변경
- live runtime restart / soak — 이전 라운드 완료 기록 있음

## Risk / Open Questions

1. **seq 12 미커밋**: `operator_autonomy.py` + test + work note가 아직 커밋/푸시되지 않음. 이번 verify 라운드에서 커밋 예정.
2. **GUI dirty (work note 미확인)**: `pipeline_gui/` 3파일 — CONTROL_SEQ 13 implement_handoff로 문서화 후 커밋 예정.
3. **`latest_verify` `—` artifact 문제**: 이전 라운드 deferred. 미해소.
4. **Axis 5b (PreferencePanel.tsx)**: GUI 정리 후 별도 라운드. 미착수.
