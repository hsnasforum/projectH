# 2026-05-18 publish held runtime doc parity guard

## 변경 파일

- `.claude/rules/pipeline-runtime.md`
- `work/5/18/2026-05-18-publish-held-runtime-doc-parity-guard.md`

## 사용 skill

- `doc-sync`: runtime/operator 동작 변경이 현재 문서 표면에 맞게 반영되어 있는지 확인하고, 빠진 고위험 운영 규칙만 좁게 보강했습니다.
- `work-log-closeout`: 구현 lane의 실제 변경 파일, 실행한 검사, 남은 리스크를 표준 `/work` 형식으로 기록했습니다.

## 변경 이유

- `CONTROL_SEQ: 1909` handoff는 publication을 held 상태로 유지한 채, dirty tracked pipeline dispatch runtime recovery 묶음의 runtime/operator 문서 parity만 확인하도록 지시했습니다.
- `.pipeline/README.md`는 `TASK_ACCEPTED`/`TASK_DONE`, `task_accept_missing`, `signal_mismatch`, `commit_push_bundle_authorization`, `operator_retriage_no_next_control`, publish backlog held 동작을 이미 상세히 설명하고 있었습니다.
- `.claude/rules/pipeline-runtime.md`의 고위험 요약에는 Codex-only 또는 `ADVISORY_DISABLED` operator retriage에서 publish backlog를 기본 보류하고 다음 non-publish local control을 써야 한다는 규칙과, `RUNTIME_STATUS_AT_DISPATCH`를 lane-local runtime command 충돌보다 우선한다는 규칙이 빠져 있어 보강했습니다.

## 핵심 변경

- `.claude/rules/pipeline-runtime.md`에 `commit_push_bundle_authorization + internal_only` 및 `PUBLISH_HELD: true` retriage에서는 commit/push/branch/PR/merge를 실행하지 않고 다음 non-publish local control을 쓰는 규칙을 추가했습니다.
- `.claude/rules/pipeline-runtime.md`에 verify/retriage prompt의 `RUNTIME_STATUS_AT_DISPATCH`를 lane-local `status --json`, `doctor --json`, tmux 접근 충돌보다 우선하는 runtime-liveness 표면으로 취급하는 규칙을 추가했습니다.
- `.pipeline/README.md`는 이미 현재 구현 truth를 담고 있어 수정하지 않았습니다.
- production code, tests, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, stash, commit/push/PR/merge/release 관련 작업은 수행하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 요청된 handoff SHA `fe2f0dc56f0ca56f1e7c4f7f06c8e8a77a939c7e98a6be2215809277383a64d2`와 일치했습니다.
- `rg -n "runtime_status_at_dispatch|RUNTIME_STATUS_AT_DISPATCH|task_accept_missing|dispatch_send_failed|commit_push_bundle_authorization|publish backlog|signal_mismatch|TASK_ACCEPTED|TASK_DONE|verify_operator_retriage|operator_retriage_no_next_control" .pipeline/README.md .claude/rules/pipeline-runtime.md AGENTS.md`
  - 통과. `.pipeline/README.md`의 상세 runtime/operator 계약과 `.claude/rules/pipeline-runtime.md`의 새 요약 규칙을 확인했습니다.
- `rg -n "runtime_status_at_dispatch|RUNTIME_STATUS_AT_DISPATCH|task_accept_missing|dispatch_send_failed|commit_push_bundle_authorization|signal_mismatch|TASK_ACCEPTED|TASK_DONE|verify_operator_retriage|operator_retriage_no_next_control|PUBLISH_HELD|publish" watcher_prompt_assembly.py watcher_core.py watcher_dispatch.py verify_fsm.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_verify_fsm.py`
  - 통과. handoff의 read-only evidence scope 안에서 구현 및 테스트 표면이 문서화 대상 동작을 포함함을 확인했습니다.
- `git status --short -- .pipeline/README.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-runtime-doc-parity-guard.md`
  - closeout 작성 전 기준 `.claude/rules/pipeline-runtime.md`만 modified 상태임을 확인했습니다.
- `git diff --check -- .pipeline/README.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-runtime-doc-parity-guard.md`
  - closeout 작성 전 기준 출력 없이 통과했습니다.
- `git diff -- .claude/rules/pipeline-runtime.md`
  - 통과. 변경 범위가 두 개 bullet 추가로 제한되어 있음을 확인했습니다.
- `git status --short -- .pipeline/README.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-runtime-doc-parity-guard.md`
  - closeout 작성 후 기준 `.claude/rules/pipeline-runtime.md` modified와 새 `/work` closeout untracked만 표시했습니다.
- `git diff --check -- .pipeline/README.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-runtime-doc-parity-guard.md`
  - closeout 작성 후 기준 출력 없이 통과했습니다.
- `git status --short -- .pipeline/advisory_request.md .pipeline/operator_request.md .pipeline/implement_handoff.md`
  - 통과. 이번 implement 라운드에서 control slot 변경은 없었습니다.
- `git diff --stat -- .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-runtime-doc-parity-guard.md`
  - 통과. 추적 파일 기준 `.claude/rules/pipeline-runtime.md | 2 ++`로 확인했습니다.

## 남은 리스크

- 전체 unittest, Playwright, `make e2e-test`, local socket/server startup, live tmux E2E, long soak는 실행하지 않았습니다. 이번 handoff는 docs-parity guard이며 production code/test 변경을 하지 않았기 때문입니다.
- dirty tracked source/test 7개 파일은 이번 라운드에서 수정하거나 분리하지 않았습니다.
- `stash@{0}`는 적용/삭제/검증하지 않았습니다.
- publication은 계속 held 상태입니다. commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication, readiness claim은 수행하지 않았습니다.
