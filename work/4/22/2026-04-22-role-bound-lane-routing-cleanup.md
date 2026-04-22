# 2026-04-22 role-bound lane routing cleanup

## 변경 파일
- `pipeline_runtime/lane_catalog.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `watcher_dispatch.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/4/22/2026-04-22-role-bound-lane-routing-cleanup.md`

## 사용 skill
- `security-gate`: watcher/supervisor runtime control routing 변경의 안전 경계 확인
- `doc-sync`: 기존 runtime 문서가 lane catalog / role owner 경계를 이미 설명하는지 확인
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크 기록

## 변경 이유
- 설정값과 fixture에 남아 있는 `Claude` / `Codex` / `Gemini` 이름은 현재 physical adapter catalog로 유지하되, runtime routing logic이 그 이름을 직접 다시 해석하면 향후 adapter 추가나 role binding 변경 때 drift가 생깁니다.
- supervisor-managed watcher launch 경로, watcher read-first/pane-target/lane-status 경로, pending signal mismatch 경로에서 role owner와 lane catalog를 더 직접 사용하도록 정리했습니다.
- 서브에이전트 조사 결과도 같은 축을 지적했습니다: 이번 라운드는 fixed owner branch 제거와 shared helper 경계 강화가 가장 작은 coherent slice입니다.

## 핵심 변경
- `pipeline_runtime/lane_catalog.py`에 `legacy_watcher_pane_target_arg_for_lane()`를 추가해 watcher legacy pane target CLI flag 매핑을 catalog-owned helper로 중앙화했습니다.
- `pipeline_runtime/supervisor.py`의 watcher pane 인자 생성은 더 이상 `pane_for_lane("Codex"|"Claude"|"Gemini")`를 직접 호출하지 않고, active `runtime_lane_configs` / lane catalog를 순회합니다.
- `watcher_core.py`는 owner별 root memory 파일을 직접 분기하지 않고 `read_first_doc_for_owner()`를 사용하며, pane target / lane status fallback도 `runtime_lane_configs` 또는 `physical_lane_order()`를 봅니다.
- live session arbitration snapshot key를 `claude/codex/gemini`가 아니라 `implement/verify/advisory` role key로 바꿨습니다.
- `watcher_dispatch.py`의 pending signal mismatch fallback은 role -> fixed vendor kind 매핑 대신 `role_owner()`를 우선 사용합니다.
- `tests/test_pipeline_runtime_supervisor.py`에 watcher pane args가 fixed owner name이 아니라 lane config name을 `pane_for_lane()`에 넘기는 회귀 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile watcher_core.py watcher_dispatch.py pipeline_runtime/supervisor.py pipeline_runtime/lane_catalog.py` 통과
- `python3 -m unittest tests.test_watcher_core.RuntimePlanConsumptionTest tests.test_watcher_core.WatcherPromptAssemblyTest` 통과 (`16 tests`)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_gui_setup_profile` 통과 (`158 tests`)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_watcher_core.RuntimePlanConsumptionTest tests.test_watcher_core.WatcherPromptAssemblyTest tests.test_pipeline_gui_setup_profile` 통과 (`175 tests`)
- `python3 -m unittest tests.test_watcher_core` 통과 (`185 tests`)
- `git diff --check` 통과

## 남은 리스크
- `claude_handoff.md`, `gemini_request.md`, `gemini_advice.md` 같은 historical control filenames는 이번 범위에서 유지했습니다.
- `lane_catalog.py`, `lane_surface.py`, token usage, setup fixtures, provider dispatch functions에는 provider/adapter 이름이 남아 있습니다. 이들은 설정/adapter surface라 이번 변경의 제거 대상이 아닙니다.
- 당시 남은 legacy route label(`codex_followup` / `codex_triage`) 정규화는 후속 `verify-route-label-normalization` slice에서 처리했습니다.
