STATUS: verified
CONTROL_SEQ: 16
BASED_ON_WORK: work/4/23/2026-04-23-runtime-pr-merge-recovery-routing.md
HANDOFF_SHA: pending-commit
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 14

## Claim (seq 15 — runtime PR merge recovery routing)

`pipeline_runtime/automation_health.py`:
- `VERIFY_FOLLOWUP_REASONS`에 `pr_merge_completed`, `pr_merge_head_mismatch` 추가 (+2 lines)

`pipeline_runtime/supervisor.py`:
- `_DUPLICATE_HANDOFF_BLOCK_REASONS` frozenset 추가 (handoff_already_completed / already_done / already_implemented)
- `_surface_turn_state_for_stale_operator_control()`: stale operator control 해소 후 idle/operator-wait을 `VERIFY_FOLLOWUP` turn state로 노출

`watcher_core.py`:
- `_operator_recovery_without_idle_marker()`: idle marker 없이 recoverable operator control 감지
- `_operator_recovery_key()` / `_route_operator_recovery()`: 중복 recovery dispatch 방지

**추가 발견 (work note 누락):**
- `tests/test_pipeline_runtime_automation_health.py`: +36 lines — `pr_merge_completed` → verify_followup 검증, `pr_merge_gate` (미완료) → pr_boundary 유지 검증
- `tests/test_pipeline_runtime_supervisor.py`: +156 lines — 새 supervisor 동작 검증 (stale task ignoring 등)
- `tests/test_watcher_core.py`: +66 lines — watcher recovery routing 검증

## Checks Run

- `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py` → OK
- `python3 -m py_compile tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py` → OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v` → **358/358 OK**
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py` → OK

## Work Note Truth Gap

작업 노트가 3개 테스트 파일(automation_health, supervisor, watcher_core)을 변경 파일 목록에서 누락했습니다. 333 tests 주장은 실제 358 tests로 정정됩니다.

## 이전 라운드 요약

- PR #29 merged (seqs 12–13: parser fix + GUI automation-health presenter) → main 포함
- seq 12: `referenced_operator_pr_numbers()` structured field 우선 파싱 (CONTROL_SEQ 8–9 루프 수정)
- seq 13: `build_control_presentation()` automation_health 기반 표시

## 현재 브랜치 상태 (커밋 전)

- HEAD: `ca6333f` (PR #29 merge 이후, 이미 main에 포함)
- **미커밋**: runtime 3파일 + test 3파일 + work note (seq 15 scope)
- `latest_verify` `—` artifact 문제: 이전 라운드 deferred, 미해소
- **Axis 5b (PreferencePanel.tsx)**: M13 Axis 5 백엔드 완료 후 대기 중인 프론트엔드 슬라이스

## Checks Not Run

- live runtime restart / soak — 이번 변경이 unit test 전용 routing surface; 이전 라운드 기록 있음
- Playwright E2E — browser-visible contract 미변경

## Risk / Open Questions

1. **미커밋**: seq 15 파일들 이번 verify 라운드에서 커밋 예정.
2. **새 PR 필요**: 커밋 이후 main 대비 새 커밋이 생김.
3. **Axis 5b**: CONTROL_SEQ 16 implement_handoff → PreferencePanel.tsx에 reliability_stats 표시.
4. **`latest_verify` artifact**: 계속 deferred.
