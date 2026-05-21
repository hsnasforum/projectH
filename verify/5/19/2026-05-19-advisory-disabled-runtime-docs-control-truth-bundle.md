# 2026-05-19 advisory disabled runtime docs control truth bundle verify

STATUS: verified

## 대상

- 최신 `/work`: `work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md`
- 이전 기준 `/verify`: `verify/5/19/2026-05-19-advisory-disabled-runtime-aggregate-guard.md`
- 목적: advisory-disabled runtime docs/control truth bundle의 진실성 확인

## 결론

- 최신 `/work`의 `## 변경 파일`은 `.pipeline/README.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`, 새 `/work` closeout이며 현재 scoped status와 일치합니다.
- `.pipeline/README.md`는 `stale_control_advisory`를 advisory-enabled profile의 `advisory_followup`과 Codex-only `advisory_enabled=false` profile의 `verify_followup`으로 분리해 현재 `_followup_action(...)` 구현과 맞췄습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`도 stale operator stop / no-silent-stall 설명에 같은 advisory-disabled routing 예외를 반영했습니다.
- `pr_merge_completed` 이후 반복 docs-only/local guard 수렴 문구는 commit/push/PR/merge 작업을 implement lane에 넘기지 않는 현재 contract와 충돌하지 않습니다.
- `RUNTIME_STATUS_AT_DISPATCH`는 이번 verify dispatch에서 `runtime_state=RUNNING`, `automation_health=ok`, `automation_next_action=continue`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 제공됐습니다. lane-local runtime/status/tmux 명령은 사용하지 않았습니다.

## 실행한 검증

- PASS: `git diff --check -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- CHECK: `git diff --check --no-index /dev/null work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- CHECK: `git status --short -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `.pipeline/README.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` 수정과 새 `/work` closeout만 표시됐습니다.
- CHECK: `git status --short`
  - runtime source/test/docs 변경과 같은 날 `/work`/`/verify` untracked notes가 남아 있음을 확인했습니다.

## 실행하지 않은 검증

- 이번 최신 `/work`는 docs-only truth-sync이므로 unit, Playwright/E2E, `make e2e-test`, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- lane-local `status --json`, `doctor --json`, `tmux` 명령은 `RUNTIME_STATUS_AT_DISPATCH`가 authoritative surface로 제공되어 실행하지 않았습니다.

## Council 결정

COUNCIL_DECISION: operator_required
REASON_CODE: commit_push_bundle_authorization
OWNER_ROLE: operator
NEXT_CONTROL_FILE: .pipeline/operator_request.md
NEXT_CONTROL_SEQ: 1955

EVIDENCE:

- `work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md`
- `verify/5/19/2026-05-19-advisory-disabled-runtime-aggregate-guard.md`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `watcher_prompt_assembly.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`

REJECTED:

- implement_handoff for commit/push/PR: implement prompts forbid commit, push, branch publication, PR creation/reuse/update, merge, and release work.
- advisory_request: `ADVISORY_ENABLED=false` 조건이므로 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- Gemini/advisory follow-up: 남은 결정은 external publication/hold 여부인 operator-only boundary이고, advisory도 비활성화되어 local council evidence로 수렴했습니다.
- another docs-only micro-slice: 같은 날 same-family docs-only/local-guard 라운드가 이미 반복됐고, 이번 bounded docs bundle이 두 runtime docs를 함께 닫았습니다.
- another runtime unit guard: 직전 aggregate guard가 focused runtime unit 묶음을 통과했습니다.

## 다음 상태

- `.pipeline/operator_request.md#1955`로 verified advisory-disabled runtime automation bundle의 commit/push/PR publication을 승인할지, 아니면 publication을 계속 보류하고 다음 local-only slice를 지시할지 operator decision을 요청하는 것이 맞습니다.
- 이 verify prompt에서는 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release를 수행하지 않았습니다.
