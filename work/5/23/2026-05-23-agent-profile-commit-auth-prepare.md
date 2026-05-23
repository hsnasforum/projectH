# 2026-05-23 agent profile commit auth prepare

## 변경 파일
- `.pipeline/config/agent_profile.json`
- `CLAUDE.md`
- `GEMINI.md`
- `.pipeline/README.md`
- `work/5/23/2026-05-23-agent-profile-commit-auth-prepare.md`

## 사용 skill
- `doc-sync`: 현재 two-agent runtime profile과 root/pipeline 문서의 role binding 설명을 맞추기 위해 사용했습니다.
- `work-log-closeout`: 검사 범위, 실제 변경, 검증 결과, commit authorization readiness를 `/work` closeout으로 기록하기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2156의 `agent_profile_commit_auth_prepare` 지시에 따라 `.pipeline/config/agent_profile.json`의 dirty two-agent profile이 현재 runtime truth와 내부적으로 일치하는지 확인해야 했습니다.
- 현재 profile은 `selected_agents=["Codex","Claude"]`, `implement=Codex`, `verify=Claude`, `advisory=Codex`, `advisory_enabled=true`, `single_agent_mode=false`입니다.
- 이전 Codex-only 운영 설명이 root/pipeline 문서에 남아 있으면 향후 commit authorization 전에 profile truth가 모호해질 수 있어 최소 문서 동기화가 필요했습니다.

## 핵심 변경
- `CLAUDE.md`의 Role Binding 섹션을 현재 Codex+Claude two-agent profile로 업데이트했습니다.
- `GEMINI.md`의 advisory role 설명을 현재 profile에서는 Gemini가 선택되지 않았고 advisory owner가 Codex라는 사실에 맞췄습니다.
- `.pipeline/README.md`의 현재 tmux lane 예시와 smoke helper profile 설명을 현재 운영 profile 값에 맞췄습니다.
- `.pipeline/README.md`의 Codex-only 관련 publish/advisory 문구는 현재 profile 단정이 아니라 조건부 profile 규칙으로 남도록 정리했습니다.
- `.claude/rules/pipeline-runtime.md`는 검사했지만 현재 active profile을 Codex-only로 단정하는 문구가 없어 수정하지 않았습니다.
- `AGENTS.md`와 `PROJECT_CUSTOM_INSTRUCTIONS.md`도 검색했으며, 남은 Codex-only 문구는 `advisory_enabled=false` 같은 조건부 profile 규칙이라 수정하지 않았습니다.

## 검증
- 통과: `python3 -m json.tool .pipeline/config/agent_profile.json`
- 통과: `python3 -c "import json; from pathlib import Path; from pipeline_gui.setup_profile import resolve_project_runtime_adapter; adapter=resolve_project_runtime_adapter(Path('.').resolve()); print(json.dumps({'controls': adapter.get('controls'), 'role_owners': adapter.get('role_owners'), 'prompt_owners': adapter.get('prompt_owners'), 'enabled_lanes': adapter.get('enabled_lanes')}, sort_keys=True))"`
  - 결과: enabled lanes `["Claude","Codex"]`, role/prompt owners `implement=Codex`, `verify=Claude`, `advisory=Codex`, `advisory_enabled=true`
- 통과: `python3 -m py_compile watcher_core.py watcher_recovery.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: 283 tests OK
- 통과: `git diff --check -- .pipeline/config/agent_profile.json CLAUDE.md GEMINI.md .pipeline/README.md`
- 통과: `git diff --check -- .pipeline/config/agent_profile.json CLAUDE.md GEMINI.md .pipeline/README.md work/5/23/2026-05-23-agent-profile-commit-auth-prepare.md`
- 확인: `rg -n "current .*Codex-only|current Codex-only|현재 .*Codex-only|현재 운영 profile|current local launcher profile|selected_agents=\\[\\\"Codex\\\"\\]|advisory=\\\"\\\"|advisory_enabled=false|verify=Codex" AGENTS.md PROJECT_CUSTOM_INSTRUCTIONS.md CLAUDE.md GEMINI.md .pipeline/README.md .claude/rules/pipeline-runtime.md`
  - 결과: 현재 active profile 단정으로 남은 Codex-only 문구 없음. 남은 Codex-only 문구는 조건부 profile 규칙입니다.

## 남은 리스크
- commit/push/PR은 실행하지 않았습니다. 이번 slice는 commit authorization 준비와 문서 truth sync까지만 수행했습니다.
- `.pipeline/config/agent_profile.json`은 현재 운영 배포 설정을 담은 dirty 파일입니다. commit 대상 포함 여부는 별도 publish authorization 경계에서 확정해야 합니다.
- A3 Step 8 관련 dirty state(`watcher_core.py`, `watcher_recovery.py`, `tests/test_watcher_recovery.py`, `work/5/22/...`)와 기존 `report/gemini/` advisory 기록은 이번 slice 범위 밖이라 수정하지 않았습니다.
- 현재 profile과 문서 truth는 commit authorization 검토에 들어갈 준비가 되었지만, 실제 commit/push/PR 실행은 별도 명시 승인 없이는 진행하지 않습니다.
