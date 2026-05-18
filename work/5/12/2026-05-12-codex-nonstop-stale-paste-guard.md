# 2026-05-12 Codex 단독 non-stop stale paste guard

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/automation_health.py`
- `watcher_dispatch.py`
- `watcher_core.py`
- `watcher_prompt_assembly.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `.pipeline/config/agent_profile.json`
- `.pipeline/config/agent_profile.draft.json`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/5/12/2026-05-12-codex-nonstop-stale-paste-guard.md`

## 사용 skill
- `security-gate`
- `doc-sync`
- `work-log-closeout`
- `release-check`

## 변경 이유
- Codex 단독 운영에서 `publish_boundary_accumulated_dirty_tree`와 `commit_push_bundle_authorization` 계열이 operator hibernate 또는 stale pasted prompt 루프로 멈추는 문제를 재발 방지하기 위해 수정했습니다.
- Claude advisory를 기본 경로에서 빼고 Codex가 implement/verify follow-up을 맡는 active profile로 고정했습니다.

## 핵심 변경
- Codex pane에 `[Pasted Content ...]`가 남아 있으면 hard clear 후 marker가 사라진 경우에만 paste를 진행하고, 실패 또는 성공 반환 뒤 marker 잔존 시 `codex_stale_paste_blocked` event와 backoff로 표면화합니다.
- `operator_retriage_no_next_control`은 advisory disabled 상태에서 `.pipeline/advisory_request.md`를 쓰지 않고 Codex verify follow-up으로 되돌아가며, prompt에 `ADVISORY_DISABLED: true`, `PUBLISH_HELD: true`를 전달합니다.
- publish 후보 문구인 `authorize ... or explicitly hold publication`은 승인 완료가 아니라 backlog 보류 대상으로 분리했습니다.
- `verify_followup_no_next_control`, stale paste, release-gate compatibility alias에 대한 supervisor/health/test coverage를 추가했습니다.
- active `.pipeline/config/agent_profile*.json`을 Codex-only로 맞췄고, 루트/운영 문서를 현재 기본 profile에 맞게 동기화했습니다.

## 검증
- `python3 -m unittest -v tests.test_watcher_core tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest tests.test_operator_request_schema tests.test_pipeline_runtime_automation_health`
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py watcher_dispatch.py watcher_core.py watcher_prompt_assembly.py`
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py watcher_dispatch.py watcher_core.py watcher_prompt_assembly.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md AGENTS.md CLAUDE.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md .pipeline/config/agent_profile.json .pipeline/config/agent_profile.draft.json`
- live 확인: `pipeline_runtime.cli status --json`에서 `automation_health=attention`, `automation_next_action=verify_followup`, Codex lane `WORKING/followup` 확인.
- live raw log에서 stale pasted prompt가 `codex_stale_paste_blocked`와 `codex_stale_paste_backoff`로 표면화되는 것을 확인했습니다.

## 남은 리스크
- live Codex pane에는 이전 prompt 누적에서 온 queued input이 남아 있었고, 수동 clear 후 Codex가 operator retriage prompt를 받아 작업 중입니다.
- 현재 `.pipeline/operator_request.md`의 git index write/publish backlog 자체는 여전히 publication 보류 후보입니다. 이번 변경은 commit/push/PR 실행이 아니라 Codex 단독 복구와 반복 paste 방지 안정장치입니다.
