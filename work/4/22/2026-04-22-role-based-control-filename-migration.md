# 2026-04-22 role-based control filename migration

## 변경 파일
- `pipeline_runtime/schema.py`
- `watcher_core.py`
- `watcher_dispatch.py`
- `watcher_prompt_assembly.py`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/turn_arbitration.py`
- `pipeline_runtime/role_routes.py`
- `pipeline_gui/backend.py`
- `pipeline_gui/guide.py`
- `pipeline_gui/project.py`
- `pipeline_gui/setup.py`
- `scripts/pipeline_runtime_fake_lane.py`
- `scripts/pipeline_runtime_gate.py`
- `.pipeline/archive-stale-control-slots.sh`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_turn_arbitration.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_gui_backend.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `tests/test_pipeline_gui_agents.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_pipeline_slot_archive.py`
- `tests/test_pipeline_gui_setup_profile.py`
- `tests/test_pipeline_runtime_control_writers.py`
- `tests/test_pipeline_runtime_fake_lane.py`
- `tests/test_pipeline_runtime_gate.py`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.pipeline/README.md`
- `.gitignore`
- `work/README.md`
- `verify/README.md`
- `docs/projectH_pipeline_runtime_docs/00_문서세트_안내.md`
- `docs/projectH_pipeline_runtime_docs/02_요구사항_명세서.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `docs/projectH_pipeline_runtime_docs/06_ADR_아키텍처_결정기록.md`
- `docs/projectH_pipeline_runtime_docs/07_마이그레이션_체크리스트.md`
- `.pipeline/harness/advisory.md`
- `.pipeline/gui-runtime/_data/start-pipeline.sh` (gitignored packaged runtime local sync)
- `.pipeline/gui-runtime/_data/watcher_core.py` (gitignored packaged runtime local sync)
- `.pipeline/gui-runtime/_data/.pipeline/README.md` (gitignored packaged runtime local sync)
- `work/4/22/2026-04-22-role-based-control-filename-migration.md`

## 사용 skill
- `doc-sync`: role-based canonical filename 계약과 historical alias 문구를 agent docs, runtime docs, work/verify README에 맞추기 위해 사용했습니다.
- `security-gate`: runtime control slot, shell launcher, archive helper가 바뀌므로 local-first/read-only alias/approval boundary가 유지되는지 확인했습니다.
- `work-log-closeout`: 변경 사실과 실제 검증 결과를 `/work` 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`가 vendor 이름을 control-plane 계약처럼 고정해, 나중에 implement/advisory owner가 바뀔 때 혼동과 하드코딩 위험이 커지는 문제가 있었습니다.
- canonical 파일명을 `.pipeline/implement_handoff.md`, `.pipeline/advisory_request.md`, `.pipeline/advisory_advice.md`로 바꾸고, 기존 파일명은 같은 logical slot의 read-only compatibility alias로만 남겼습니다.
- watcher/supervisor/GUI/launcher가 filename 자체보다 `slot_id`와 `CONTROL_SEQ`를 기준으로 같은 control을 해석하게 해, alias와 canonical이 동시에 있어도 control plane이 둘로 갈라지지 않도록 했습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`에 `ControlSlotSpec` 기반 registry를 추가하고, parser가 `slot_id`, `canonical_file`, `is_legacy_alias`를 함께 반환하게 했습니다. 같은 logical slot에서는 높은 `CONTROL_SEQ`가 이기고, 같은 seq면 canonical 파일이 이깁니다.
- watcher dispatch/prompt path는 canonical 파일을 쓰되, pending queue drift 비교는 raw filename 대신 `expected_control_slot`과 alias-aware filename 비교를 사용하게 했습니다.
- watcher/supervisor/GUI backend는 active control을 role slot 기준으로 읽고, status/control surface에 canonical slot metadata를 보존하게 했습니다.
- `.pipeline/archive-stale-control-slots.sh`는 canonical 파일명을 우선 accepted list에 넣고, legacy alias는 마이그레이션 중 안전 archive용으로만 허용했습니다.
- agent docs, `.pipeline/README.md`, runtime docs, `work/README.md`, `verify/README.md`, GUI guide/template은 새 canonical 이름을 current contract로 설명하고, old filenames를 historical alias로만 설명하도록 동기화했습니다.
- gitignored packaged GUI runtime copy도 로컬에서 canonical filenames + alias registry read path로 맞췄습니다. 다만 `.pipeline/gui-runtime/`은 `.gitignore` 대상이라 tracked diff에는 포함되지 않습니다.
- 추가 확인에서 `CLAUDE.md`의 stale `gemini_request` 표현과 runtime 기술문서의 old control filename 묶음을 canonical 이름으로 보정했습니다.
- `.pipeline/harness/advisory.md`는 role-neutral harness 성격과 맞게 `report/gemini/`를 current advisory report path로 낮춰 표현했습니다.
- `pipeline_runtime/role_routes.py`에 notify/route/reason alias normalizer를 추가해 `claude_handoff`, `gemini_request`, `gemini_advice_followup`, `gemini_advisory_recovery`, `codex_followup`, `codex_triage`, `codex_triage_only`가 runtime 내부에서는 role-based canonical 값으로 수렴하게 했습니다.
- watcher runtime reason과 raw event surface에서 `startup_turn_claude/gemini/codex`, `claude_idle_timeout`, `claude_activity_detected`, `claude_implement_blocked`를 `startup_turn_implement/advisory/verify`, `implement_idle_timeout`, `implement_activity_detected`, `implement_blocked`로 정리했습니다.
- supervisor도 새 `implement_activity_detected` reason을 implement active evidence로 인정하게 해, verify follow-on 중 implement owner 카드가 잘못 READY로 내려가는 회귀를 막았습니다.
- 새 canonical rolling slot 파일 `.pipeline/implement_handoff.md`, `.pipeline/advisory_request.md`, `.pipeline/advisory_advice.md`는 generated control slot로 `.gitignore`에 추가했습니다.
- `.pipeline/operator_request.md`의 live rolling header는 현재 schema가 허용하는 `OPERATOR_POLICY: immediate_publish`, `DECISION_CLASS: release_gate`로 맞췄습니다. 이 파일은 generated/ignored rolling slot이므로 tracked diff에는 나오지 않습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/supervisor.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py pipeline_gui/backend.py .pipeline/gui-runtime/_data/watcher_core.py scripts/pipeline_runtime_fake_lane.py scripts/pipeline_runtime_gate.py`
  - 결과: 통과
- `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_pipeline_gui_backend`
  - 결과: `Ran 88 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest tests.test_watcher_core.BusyLaneNotificationDeferTest tests.test_watcher_core.ControlSeqAgeTrackerTest tests.test_watcher_core.RollingSignalTransitionTest`
  - 결과: `Ran 36 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 187 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 130 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_gui_home_presenter tests.test_pipeline_launcher`
  - 결과: `Ran 175 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_watcher_core tests.test_pipeline_gui_backend tests.test_pipeline_slot_archive`
  - 결과: `Ran 277 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_setup_profile tests.test_pipeline_runtime_control_writers tests.test_pipeline_runtime_fake_lane tests.test_pipeline_runtime_gate`
  - 결과: `Ran 77 tests`, `OK`; fault-check/soak sample 출력도 PASS
- `git diff --check`
  - 결과: 통과
- `python3 -m unittest tests.test_pipeline_runtime_role_harness tests.test_pipeline_runtime_schema`
  - 결과: `Ran 42 tests`, `OK`
- `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py watcher_dispatch.py pipeline_runtime/role_routes.py pipeline_runtime/turn_arbitration.py pipeline_runtime/schema.py pipeline_runtime/supervisor.py pipeline_gui/backend.py pipeline_gui/legacy_backend_debug.py tests/test_watcher_core.py tests/test_turn_arbitration.py tests/test_pipeline_gui_backend.py tests/test_pipeline_gui_agents.py`
  - 결과: 통과
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_launcher tests.test_pipeline_gui_backend tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_agents`
  - 결과: `Ran 234 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core tests.test_turn_arbitration tests.test_operator_request_schema tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_control_writers tests.test_pipeline_runtime_role_harness tests.test_pipeline_runtime_fake_lane`
  - 결과: `Ran 265 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_active_implement_control_keeps_claude_working_even_during_verify_follow_on tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_turn_arbitration`
  - 결과: `Ran 329 tests`, `OK`
- `git diff --check -- CLAUDE.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md .pipeline/harness/advisory.md`
  - 결과: 통과
- `rg -n -e 'choose \`gemini_request\`' -e 'canonical control\\(\`claude_handoff' -e 'canonical control\\(.*gemini_request' -e 'Write one advisory report under \`report/gemini/\`' CLAUDE.md docs/projectH_pipeline_runtime_docs .pipeline/harness AGENTS.md PROJECT_CUSTOM_INSTRUCTIONS.md .pipeline/README.md`
  - 결과: 추가 stale 표현 없음

## 남은 리스크
- historical alias 파일은 삭제하지 않았습니다. legacy alias 제거, 실제 파일 archive/rename, 오래된 run snapshot 재작성은 후속 slice로 남깁니다.
- 내부 runtime reason/notify 표면은 role-based canonical 이름으로 정리했습니다. 남은 `claude_handoff` / `gemini_request` / `gemini_advice` / `codex_*` 문자열은 compatibility registry, legacy alias 테스트, historical alias 설명, 기존 generated snapshot fixture에 의도적으로 남긴 것입니다.
- physical lane catalog는 여전히 `Claude`, `Codex`, `Gemini` 세 lane 이름을 갖습니다. 이는 adapter plane 현 상태이며, 새 physical agent 추가나 lane catalog 일반화는 별도 migration으로 다루는 편이 안전합니다.
- `.pipeline/gui-runtime/_data`는 gitignored라 tracked diff에는 남지 않습니다. 로컬 packaged runtime은 맞춰두었지만, 배포/패키징 source of truth를 별도 tracked 위치로 승격할지는 후속 정리가 필요합니다.
- `.pipeline/harness/`, `pipeline_runtime/role_harness.py`, `pipeline_runtime/role_routes.py`, `tests/test_pipeline_runtime_role_harness.py`, 이번 `/work`/`/verify`/`report` 산출물은 아직 untracked입니다. 현재 요청 범위에서는 commit/push를 하지 않았으므로, 커밋 전에는 이 source/protocol 파일들을 포함 대상으로 다시 확인해야 합니다.
