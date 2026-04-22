# 2026-04-22 role harness protocol

## 변경 파일
- `.pipeline/harness/implement.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/advisory.md`
- `.pipeline/harness/council.md`
- `pipeline_runtime/role_harness.py`
- `watcher_prompt_assembly.py`
- `pipeline_gui/setup_profile.py`
- `pipeline_runtime/cli.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_role_harness.py`
- `tests/test_pipeline_gui_setup_profile.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/4/22/2026-04-22-role-harness-protocol.md`

## 사용 skill
- `github`: CLI-Anything GitHub repo의 HARNESS/SKILL/registry 패턴 확인
- `security-gate`: runtime prompt/control 경계 변경의 안전 범위 확인
- `doc-sync`: role protocol과 runtime 문서 동기화 범위 확인
- `skill-creator`: 새 repo skill 대신 작은 self-contained runtime harness로 두는 기준 확인
- `work-log-closeout`: 변경 사실과 검증 결과 closeout 작성

## 변경 이유
- CLI-Anything의 self-contained `SKILL.md` / `HARNESS.md` 패턴 중 지금 pipeline 런처에 바로 도움이 되는 부분만 흡수하기 위해서입니다.
- 새 물리 에이전트를 추가하지 않고, `implement` / `verify` / `advisory` / `council` role protocol을 분리해 막힘/선택지/긴 advisory 상황을 하나의 next control로 수렴시키는 기준을 명확히 했습니다.
- Claude/Codex/Gemini 같은 adapter 이름에 더 묶이지 않도록 prompt와 runtime adapter surface에 role-neutral harness metadata를 추가했습니다.

## 핵심 변경
- `.pipeline/harness/` 아래에 role별 SOP 4개를 추가했습니다. `council.md`는 네 번째 에이전트가 아니라 막힘을 하나의 control로 줄이는 protocol로 명시했습니다.
- `watcher_prompt_assembly.py`가 implement/advisory/verify/followup/recovery prompt에 `ROLE_HARNESS`와 필요한 경우 `COUNCIL_HARNESS` 경로를 실어 보내도록 했습니다.
- `pipeline_runtime/role_harness.py`를 추가해 role harness path/spec/map을 한 helper에서 관리하게 했고, setup adapter에는 `role_harnesses` metadata를 실었습니다.
- `pipeline_runtime/supervisor.py`의 중복 prompt template을 제거하고 `watcher_prompt_assembly.py`의 shared default prompt constants를 canonical source로 사용하게 했습니다.
- 각 `.pipeline/harness/*.md` 상단에 authority disclaimer를 추가해 harness가 control slot/current truth가 아니며 active control, 최신 `/work`/`/verify`, supervisor status/events보다 우선하지 않음을 self-contained하게 명시했습니다.
- `.pipeline/harness/*.md`에 `STATUS:` / `CONTROL_SEQ:` 같은 문구가 있어도 `parse_control_slots()`가 active control로 잡지 않는 회귀 테스트를 추가했습니다.
- supervisor/CLI watcher self-reload source 목록에 새 helper를 포함해 런타임 재시작 경계에서 코드 변경을 놓치지 않게 했습니다.
- `.pipeline/README.md`, runtime 기술설계/RUNBOOK, AGENTS/CLAUDE/GEMINI/PROJECT_CUSTOM_INSTRUCTIONS에 harness가 control slot이 아니라 role protocol임을 동기화했습니다.

## 검증
- `python3 -m py_compile watcher_prompt_assembly.py pipeline_gui/setup_profile.py pipeline_runtime/role_harness.py pipeline_runtime/cli.py pipeline_runtime/supervisor.py` 통과
- `python3 -m py_compile watcher_prompt_assembly.py pipeline_runtime/supervisor.py pipeline_runtime/role_harness.py pipeline_gui/setup_profile.py` 통과
- `python3 -m unittest tests.test_pipeline_runtime_role_harness tests.test_pipeline_gui_setup_profile tests.test_watcher_core.WatcherPromptAssemblyTest` 통과
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_role_harness tests.test_pipeline_gui_setup_profile tests.test_watcher_core.WatcherPromptAssemblyTest tests.test_pipeline_runtime_schema` 통과 (`204 tests`)
- `python3 -m unittest tests.test_watcher_core tests.test_pipeline_gui_setup_profile tests.test_pipeline_runtime_role_harness` 통과 (`216 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 slice는 CLI-Anything의 full CLI-Hub/registry 설치 흐름을 들여오지 않았습니다. 지금은 role protocol과 prompt/read-model metadata만 흡수했습니다.
- physical lane catalog는 여전히 `Claude`, `Codex`, `Gemini` 세 lane 기준입니다. 향후 adapter 추가는 `lane_catalog` / setup profile / wrapper 쪽에서 별도 coherent slice로 다뤄야 합니다.
- harness 문서는 prompt reference이지 supervisor state authority가 아닙니다. 실제 자동 회의/수렴 강제는 이후 advisory budget, verify takeover, priority guard slice에서 더 고정해야 합니다.
- 다음 자동화 우선순위는 product milestone next-slice가 아니라 pipeline launcher / watcher 자동화 안정화입니다. 후속 `/verify`와 `.pipeline/claude_handoff.md`는 이 방향을 기준으로 남겨야 합니다.
- 작업 전부터 `work/4/22/2026-04-22-publish-bundle-closeout.md` untracked 파일이 있었고, 이번 변경에서는 건드리지 않았습니다.
