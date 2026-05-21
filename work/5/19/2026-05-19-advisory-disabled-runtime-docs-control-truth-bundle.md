# 2026-05-19 advisory disabled runtime docs control truth bundle

## 변경 파일

- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md`

## 사용 skill

- `work-log-closeout`: handoff 수행 결과, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1954`가 advisory-disabled runtime control behavior를 두 runtime docs와 현재 구현/test truth에 맞춰 한 번에 닫으라고 지시했습니다.
- 기존 docs diff는 publish/PR/merge 작업을 implement lane에 넘기지 않는 방향과 맞았지만, stale-control advisory grace가 `advisory_enabled=false` profile에서 `verify_followup`으로 표면화되는 예외가 문서에 명시되지 않았습니다.
- implement lane 지시에 따라 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release는 수행하지 않았고 다음 slice도 선택하지 않았습니다.

## 핵심 변경

- `.pipeline/README.md`의 `stale_control_advisory` 설명을 advisory-enabled profile의 `advisory_followup`과 Codex-only `advisory_enabled=false` profile의 `verify_followup`으로 분리했습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`의 stale operator stop / no-silent-stall 설명에 동일한 advisory-disabled routing 예외를 추가했습니다.
- 이미 있던 `pr_merge_completed` 이후 반복 docs-only/local guard 수렴 문구는 유지했고, commit/push/PR/merge 작업을 implement lane에 넘기지 않는 current contract와 충돌하지 않음을 확인했습니다.
- source/test 파일은 이번 라운드에서 수정하지 않았습니다.

## 검증

- `git diff -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 두 runtime docs의 변경 범위를 확인했습니다.
- `rg -n "pr_merge_completed|ADVISORY_DISABLED|advisory_enabled|verify_followup|operator_retriage_no_next_control|commit_push_bundle_authorization|pr_creation_gate|pr_merge_gate" .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - publish/retriage/merge-gate 관련 문서 표면을 확인했습니다.
- `rg -n "pr_merge_completed|advisory_enabled|verify_followup|operator_retriage_no_next_control|commit_push_bundle_authorization|pr_creation_gate|pr_merge_gate" pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_prompt_assembly.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 문서 주장과 대조할 구현/test 표면을 확인했습니다.
- `git diff --check -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 출력 없이 통과했습니다.
- `git diff --check -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- `git diff --check --no-index /dev/null work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- `git status --short -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-advisory-disabled-runtime-docs-control-truth-bundle.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `.pipeline/README.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` 수정과 새 `/work` closeout만 표시됐습니다.

## 남은 리스크

- 이번 handoff는 docs/control truth bundle이므로 broader unittest, Playwright/E2E, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- 이번 라운드에서는 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release, external publication을 수행하지 않았습니다.
