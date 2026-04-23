# 2026-04-23 stacked branch PR policy

## 변경 파일
- `watcher_prompt_assembly.py`
- `tests/test_watcher_core.py`
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/23/2026-04-23-stacked-branch-pr-policy.md`

## 사용 skill
- `security-gate`: branch/PR publish follow-up 규칙이 merge 실행 자동화로 넓어지지 않도록 경계를 재확인했습니다.
- `finalize-lite`: 이번 규칙 변경의 실제 검증 범위와 doc sync 범위를 함께 점검했습니다.
- `work-log-closeout`: `/work` closeout 형식과 필수 항목을 맞춰 기록했습니다.

## 변경 이유
- 사용자 요청은 stacked branch/PR 운영 규칙을 지금 정리하는 것이었습니다.
- 직전 round에서 `pr_merge_gate`를 backlog로 남기고 local 구현을 계속 진행할 수 있게 바꿨지만, 그 다음 publish 단계에서 기존 pending merge PR을 계속 덧대도 되는지에 대한 기본 규칙이 명확하지 않았습니다.
- 이 기준이 없으면 verify/handoff owner가 pending merge candidate를 계속 변형해 publication truth와 PR 리뷰 단위를 흔들 수 있습니다.

## 핵심 변경
- `watcher_prompt_assembly.py`의 operator retriage prompt에, 기존 draft PR이 이미 merge 승인 backlog에 있으면 그 PR은 기본적으로 안정적으로 유지하고 다음 검증 묶음은 stacked child branch/PR로 publish하라는 규칙을 추가했습니다.
- child PR은 parent branch를 base로 열고, `/work`에 parent/child linkage를 남긴 뒤 parent merge 후 저장소 기본 base branch로 retarget하라는 운영 절차를 명시했습니다.
- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 같은 운영 규칙을 반영해 implement/verify/handoff 경계 문서와 실행 지시문을 동기화했습니다.
- runtime 기술 명세와 운영 runbook에도 stacked child branch/PR 기본 전략을 추가해, `pr_creation_gate`와 `pr_merge_gate`가 함께 있는 publish follow-up의 expected behavior를 현재 truth로 고정했습니다.

## 검증
- `python3 -m py_compile watcher_prompt_assembly.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest.test_pr_creation_gate_routes_to_verify_owner_publish_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_pr_merge_gate_internal_only_routes_to_verify_followup_backlog -v`
  - 통과: `2 tests`
- `git diff --check -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md watcher_prompt_assembly.py tests/test_watcher_core.py`
  - 통과: 출력 없음
- `python3 -m pipeline_runtime.cli status /home/xpdlqj/code/projectH --json`
  - 확인 결과: `runtime_state=RUNNING`, `automation_health=ok`, 현재 `Claude` lane이 `VERIFY_ACTIVE`로 진행 중

## 남은 리스크
- 현재 runtime은 이미 진행 중인 verify round가 있어 이번 라운드에서는 재시작하지 않았습니다. 따라서 새 watcher prompt 문구는 다음 runtime restart 이후의 fresh dispatch부터 확실히 반영됩니다.
- 이번 변경은 branch/PR 운영 규칙과 prompt 계약을 정한 것입니다. GitHub에서 실제 stacked branch 생성, child PR open, parent merge 후 retarget까지를 런타임이 자동 실행하는 단계는 아직 아닙니다.
- 일부 비권위 문서나 오래된 closeout에는 여전히 “draft PR 재사용”만 간단히 적혀 있을 수 있습니다. 이번 라운드에서는 AGENTS / mirrored instructions / runtime spec / runbook까지만 현재 truth로 맞췄습니다.
