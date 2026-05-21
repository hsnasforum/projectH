# 2026-05-19 runtime docs control truth bounded bundle

## 변경 파일

- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `work/5/19/2026-05-19-runtime-docs-control-truth-bounded-bundle.md`
- 검증 대상 기존 dirty 문서
  - `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 사용 skill

- `doc-sync`: runtime/task-hint, advisory-disabled routing, publication-held control truth를 현재 구현 및 검증 truth에 맞춰 세 문서 범위 안에서 동기화하기 위해 사용했습니다.
- `work-log-closeout`: handoff #1986의 문서 정리 범위, 실제 수정 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1986`이 task-hint aggregate unit guard 이후 현재 runtime automation docs/control truth를 하나의 bounded docs bundle로 정리하라고 지시했습니다.
- task-hint, stale verify follow-up cleanup, advisory-disabled routing, runtime status surface, publication hold, post-merge/pr-merge recovery 설명이 여러 문서에 걸쳐 있었고, 같은 narrow docs-only guard를 반복하지 않도록 현재 truth를 한 번에 맞출 필요가 있었습니다.
- publication은 계속 held 상태이며, implement lane에 commit/push/PR/merge/release 작업을 넘기지 않는 경계가 유지됩니다.

## 핵심 변경

- `.pipeline/README.md`의 알 수 없는 publish label / 구조화 metadata 누락 설명을 `fail-closed immediate needs_operator`로 맞추고, 외부 publication 실행으로 해석하지 않는다고 명시했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`에서 runtime status derived field 설명에 watcher exporter와 profile `runtime_controls`를 포함했습니다.
- 같은 기술설계 문서에서 stale-control advisory grace가 advisory-enabled profile에서는 `advisory_followup`, `advisory_enabled=false` profile에서는 `verify_followup`으로 표면화된다고 정리했습니다.
- publish follow-up은 implement lane으로 넘기지 않으며, advisory가 비활성화된 Codex-only profile에서는 publication을 held 상태로 두고 다음 safe local control로 수렴한다고 명시했습니다.
- control-recovery no-next-control path도 advisory-enabled와 advisory-disabled profile을 구분해 설명했습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`는 이번 라운드에서 새로 수정하지 않았고, 현재 dirty 내용이 위 contract와 같은 방향임을 검증 대상으로 확인했습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `c05507542ed44e5b5eec9167957037c6dcce94b91bfff9c14c5947bc5e376263`와 일치했습니다.
- `rg -n "task hint|task-hint|task_hints|task-hints|runtime_controls|automation_health|automation_next_action|advisory_disabled|advisory-disabled|PUBLISH_HELD|commit_push_bundle_authorization|pr_merge_completed|publication" .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: PASS. 세 문서에서 task hint, runtime controls/status, advisory-disabled, publication-held, pr-merge recovery 관련 현재 truth가 확인됐습니다.
- `rg -n "fail-safe immediate|fail-safe로 즉시 publish|automation_next_action=advisory_followup|advisory request로 승격|implement lane으로 넘기지 않습니다" docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: PASS. 남은 `automation_next_action=advisory_followup` 표현은 advisory-enabled profile 또는 일반 follow-up option 문맥이며, 수정 대상이던 unconditional stale-control advisory drift는 제거됐습니다.
- `git diff --check -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-runtime-docs-control-truth-bounded-bundle.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- 이번 라운드는 문서/control truth bundle입니다. production code, tests, browser UI, storage schema, approval-flow, web-investigation, reviewed-memory behavior, pipeline runtime behavior는 수정하지 않았습니다.
- `python3 -m py_compile`, `python3 -m unittest`, Playwright, `make e2e-test`, live `pipeline_runtime.cli start`, `status --json`, `doctor --json`, tmux, controller startup, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- 기존 dirty worktree에는 reviewed-memory, runtime, docs, tests 계열 변경이 넓게 남아 있습니다. 이번 handoff와 무관한 변경은 되돌리지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
