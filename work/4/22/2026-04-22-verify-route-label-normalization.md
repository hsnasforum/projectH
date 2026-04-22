# 2026-04-22 verify route label normalization

## 변경 파일
- `pipeline_runtime/role_routes.py`
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/control_writers.py`
- `pipeline_runtime/turn_arbitration.py`
- `pipeline_runtime/supervisor.py`
- `watcher_prompt_assembly.py`
- `watcher_core.py`
- `tests/test_turn_arbitration.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `work/4/22/2026-04-22-role-bound-lane-routing-cleanup.md`
- `work/4/22/2026-04-22-verify-route-label-normalization.md`

## 사용 skill
- `security-gate`: runtime control route/event/log label 변경이 operator boundary를 약화하지 않는지 확인
- `doc-sync`: prompt/runtime contract 변경을 AGENTS/CLAUDE/PROJECT instructions와 pipeline docs에 동기화
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 persistent work note로 기록

## 변경 이유
- 이전 slice에서 physical lane 이름 직접 참조는 줄였지만, verify/handoff follow-up 경로에 `codex_followup`, `codex_triage` 같은 Codex-bound legacy label이 남아 있었습니다.
- 향후 verify owner가 Codex가 아니어도 같은 runtime contract를 유지하려면 canonical route/event/prompt surface는 role-bound `verify_followup`, `verify_triage`여야 합니다.
- 기존 실행 슬롯과 오래된 pane output 호환을 위해 legacy codex label은 입력 alias로만 유지했습니다.

## 핵심 변경
- `pipeline_runtime/role_routes.py`를 추가해 `verify_followup` / `verify_triage` canonical 값과 `codex_followup` / `codex_triage` legacy alias 정규화를 한곳에 모았습니다.
- operator autonomy 출력, turn arbitration, supervisor duplicate marker, watcher prompt dispatch notify kind를 `verify_*` 계열로 전환했습니다.
- implement blocked sentinel 기본 prompt와 agent instructions를 `REQUEST: verify_triage`, `ESCALATION_CLASS: verify_triage`로 갱신했습니다.
- watcher는 legacy `codex_triage`, `codex_triage_only`, `codex_followup`, `codex_operator_retriage` 입력을 읽을 수 있지만 새 surface에는 canonical verify label을 씁니다.
- `.pipeline/README.md`와 runtime 기술설계 문서에 legacy codex label은 호환 alias이고 새 runtime surface는 verify label이라는 계약을 추가했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/role_routes.py pipeline_runtime/operator_autonomy.py pipeline_runtime/control_writers.py pipeline_runtime/turn_arbitration.py pipeline_runtime/supervisor.py watcher_prompt_assembly.py watcher_core.py` 통과
- `python3 -m unittest tests.test_turn_arbitration tests.test_watcher_core.WatcherPromptAssemblyTest` 통과 (`15 tests`)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` 통과 (`130 tests`)
- `python3 -m unittest tests.test_watcher_core` 통과 (`186 tests`)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_schema tests.test_turn_arbitration tests.test_pipeline_launcher tests.test_pipeline_gui_home_presenter` 통과 (`220 tests`)
- `git diff --check` 통과
- 초기 focused command에서 존재하지 않는 테스트 클래스명(`WatcherOperatorGateTest`, `OperatorAutonomyClassifierTest`)을 지정해 실패했고, 실제 클래스/모듈 기준으로 재실행해 통과를 확인했습니다.

## 남은 리스크
- `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md` historical control filename은 아직 유지됩니다.
- `watcher_core.py`의 legacy config key(`codex_blocked_triage_prompt`)와 legacy pending notify kind alias(`codex_operator_retriage`)는 기존 런타임 큐/설정 호환을 위해 읽기 전용 alias로 남겼습니다.
- `lane_surface.py`의 Codex/Gemini activity detector와 adapter dispatch 함수명은 physical adapter plane에 속하므로 이번 role-route label 정규화 범위 밖입니다.
