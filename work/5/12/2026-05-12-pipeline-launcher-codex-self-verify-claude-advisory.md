# 2026-05-12 파이프라인 런처 Codex self-verify / Claude advisory 전환

## 변경 파일

- `.pipeline/README.md`
- `.pipeline/config/agent_profile.draft.json`
- `.pipeline/config/agent_profile.json`
- `.pipeline/harness/advisory.md`
- `.pipeline/setup/apply.json`
- `.pipeline/setup/last_applied.json`
- `.pipeline/setup/preview.json`
- `.pipeline/setup/request.json`
- `.pipeline/setup/result.json`
- `.pipeline/smoke-three-agent-arbitration.sh`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `pipeline_gui/app.py`
- `pipeline_gui/setup.py`
- `pipeline_gui/setup_controller.py`
- `pipeline_runtime/lane_catalog.py`
- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_gui_app.py`
- `tests/test_pipeline_gui_setup_controller.py`
- `tests/test_pipeline_runtime_gate.py`
- `work/5/12/2026-05-12-pipeline-launcher-codex-self-verify-claude-advisory.md`

## 사용 skill

- `onboard-lite`: 파이프라인 런처, setup controller, runtime adapter, active profile의 실제 진입점을 좁혀 확인했습니다.
- `security-gate`: 역할 바인딩, 런처 프로필, shell 실행 인자, control slot 경계가 approval/local-first 원칙을 벗어나지 않는지 점검했습니다.
- `doc-sync`: root memory, Claude/Gemini role memory, pipeline README, advisory harness, setup template 문구를 현재 역할 배치와 동기화했습니다.
- `finalize-lite`: 구현 후 관련 테스트, 문서 동기화, closeout 준비 상태를 점검했습니다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 표준 `/work` 형식으로 기록했습니다.

## 변경 이유

- 사용자가 파이프라인 런처의 구현 및 검증 역할을 Codex로 두고, advisor 역할을 Claude로 바꾸고 싶다고 요청했습니다.
- 기존 기본 role binding은 구현/검증/advisory가 서로 다른 소유자 전제를 강하게 갖고 있었고, active profile도 Gemini까지 선택된 형태였으므로 런처 기본값, 현재 적용 프로필, 문서/테스트를 함께 맞출 필요가 있었습니다.

## 핵심 변경

- 기본 role binding을 `implement=Codex`, `verify=Codex`, `advisory=Claude`로 전환했습니다.
- setup controller와 GUI 기본 선택값이 실제 role owner 집합만 선택하도록 바꿔 기본 선택 agent를 `Claude`, `Codex`로 제한하고 Gemini는 disabled/unselected 상태로 두었습니다.
- self-verify 구성이므로 active/default profile에 `self_verify_allowed=true`를 반영했고, resolver는 `ready / experimental / launch_allowed=true`로 해석합니다.
- runtime gate와 live arbitration smoke의 synthetic profile 생성도 role binding 기반으로 맞췄고, advisory/verify pane 진단은 실제 owner pane을 보도록 일반화했습니다.
- `.pipeline/config` 및 `.pipeline/setup` 기록을 새 setup id `setup-20260512-124049-codex-selfverify` 기준으로 갱신했습니다.
- `CLAUDE.md`는 Claude가 advisory owner일 때의 쓰기 경계와 금지 범위를 추가했고, `GEMINI.md`는 현재 profile에서 Gemini가 비선택 상태임을 명시했습니다.

## 검증

- PASS: `python3 -m json.tool .pipeline/config/agent_profile.json >/dev/null && python3 -m json.tool .pipeline/config/agent_profile.draft.json >/dev/null && python3 -m json.tool .pipeline/setup/request.json >/dev/null && python3 -m json.tool .pipeline/setup/preview.json >/dev/null && python3 -m json.tool .pipeline/setup/apply.json >/dev/null && python3 -m json.tool .pipeline/setup/result.json >/dev/null && python3 -m json.tool .pipeline/setup/last_applied.json >/dev/null`
- PASS: `python3 - <<'PY' ... resolve_project_active_profile / resolve_project_runtime_adapter / SetupController.reconcile_last_applied ... PY`
  - 확인 결과: `profile ready experimental True`
  - 확인 결과: `enabled_lanes ['Claude', 'Codex']`
  - 확인 결과: `role_owners {'implement': 'Codex', 'verify': 'Codex', 'advisory': 'Claude'}`
  - 확인 결과: `lane_roles {'Claude': ['advisory'], 'Codex': ['implement', 'verify'], 'Gemini': []}`
  - 확인 결과: `reconcile ok`
- PASS: `python3 -m unittest -v tests.test_pipeline_gui_setup_profile tests.test_pipeline_gui_setup_controller tests.test_pipeline_runtime_gate.PipelineRuntimeGateSoakTest.test_prepare_synthetic_workspace_seeds_profile_and_work_note tests.test_pipeline_runtime_gate.PipelineRuntimeGateSoakTest.test_write_active_profile_accepts_legacy_override tests.test_pipeline_gui_app.PipelineGuiAppTest.test_setup_refresh_uses_active_profile_as_applied_truth_without_runtime_artifacts tests.test_pipeline_gui_app.PipelineGuiAppTest.test_sync_start_button_state_allows_experimental_launch_with_notice tests.test_pipeline_gui_app.PipelineGuiAppTest.test_setup_experimental_preview_shows_banner_and_keeps_apply_enabled`
- PASS: `python3 -m py_compile pipeline_runtime/lane_catalog.py pipeline_gui/setup_controller.py pipeline_gui/app.py pipeline_gui/setup.py scripts/pipeline_runtime_gate.py`
- PASS: `bash -n .pipeline/smoke-three-agent-arbitration.sh .pipeline/smoke-implement-blocked-auto-triage.sh`
- PASS: `git diff --check -- .pipeline/README.md .pipeline/config/agent_profile.draft.json .pipeline/config/agent_profile.json .pipeline/harness/advisory.md .pipeline/setup/apply.json .pipeline/setup/last_applied.json .pipeline/setup/preview.json .pipeline/setup/request.json .pipeline/setup/result.json .pipeline/smoke-three-agent-arbitration.sh AGENTS.md CLAUDE.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md pipeline_gui/app.py pipeline_gui/setup.py pipeline_gui/setup_controller.py pipeline_runtime/lane_catalog.py scripts/pipeline_runtime_gate.py tests/test_pipeline_gui_app.py tests/test_pipeline_gui_setup_controller.py tests/test_pipeline_runtime_gate.py`
- PASS: `python3 -m unittest -v tests.test_pipeline_gui_setup tests.test_pipeline_gui_backend tests.test_pipeline_gui_agents tests.test_pipeline_launcher`
- PASS: `python3 -m unittest -v tests.test_controller_server tests.test_pipeline_gui_home_controller`
- FAIL 후 정정: `python3 -m unittest -v tests.test_pipeline_gui_app.PipelineGuiSetupTest...`는 존재하지 않는 테스트 클래스명으로 실패했고, 올바른 `PipelineGuiAppTest` 대상 테스트를 다시 실행해 통과했습니다.
- FAIL 후 정정: profile 확인용 Python snippet 3회는 잘못된 import/module key/function signature 사용으로 실패했고, 같은 확인 목적은 위의 최종 `SetupController` 기반 snippet에서 통과했습니다.

## 남은 리스크

- live launcher/tmux smoke와 브라우저 E2E는 실행하지 않았습니다. 이번 변경은 역할 프로필, 런처 기본값, setup 기록, unit/syntax 계약 중심 변경이라 좁은 Python/unit/shell syntax 검증으로 제한했습니다.
- self-verify 구성은 의도적으로 `experimental` support level입니다. 런처는 실행 가능하지만 UI/기록에는 추가 주의 banner가 유지됩니다.
- `.pipeline/setup/last_applied.json`의 `restart_required`는 `true`입니다. 이미 떠 있는 런처/컨트롤러 세션은 새 profile을 쓰려면 재시작이 필요합니다.
- `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `tests/test_smoke.py`와 다수의 `report/`, `work/`, `verify/` untracked 항목은 작업 시작 전부터 있던 별도 변경으로 보고 건드리지 않았습니다.
