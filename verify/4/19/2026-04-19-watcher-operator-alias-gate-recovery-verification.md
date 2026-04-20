# 2026-04-19 watcher operator alias gate recovery verification

## 변경 파일
- `verify/4/19/2026-04-19-watcher-operator-alias-gate-recovery-verification.md`

## 사용 skill
- `round-handoff`: prompt가 가리킨 `/work`(`work/4/19/2026-04-19-watcher-operator-alias-gate-recovery.md`)를 현재 tree와 대조해 truth를 재확인하고, 같은 날 직전 verify(`agent-loop-conflict-labeling-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `work/4/19/2026-04-19-watcher-operator-alias-gate-recovery.md`(20:41)는 같은 날 다른 family 라운드들 사이에서 verify가 누락된 채 남아 있었습니다. operator request에서 명시적으로 verify 대상으로 지목되어, 이미 tree에 들어간 alias 정규화 + live unstick + doc sync 묶음이 truthful한지 한 번 고정해야 했습니다.
- 같은 날 직전 verify(`verify/4/19/2026-04-19-agent-loop-conflict-labeling-verification.md`)는 다른 family(`agent_loop CONFLICT plumbing`)이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `pipeline_runtime/operator_autonomy.py:141`이 `"gemini_axis_switch_without_exact_slice": "slice_ambiguity"` reason-code alias를 정규화합니다.
  - `pipeline_runtime/operator_autonomy.py:151-156`에 `gate`/`gate24h`/`gate_24`/`stop_until_truth_sync`/`stop_until_exact_slice_selected`/`stop_until_exact_slice_selection` policy alias가 모두 `"gate_24h"`로 정규화됩니다.
  - `pipeline_runtime/operator_autonomy.py:27`이 `slice_ambiguity` reason-code를 `mode=triage, routed_to=codex_followup`으로 분류해, alias-normalized 상태에서 hard publish 대신 gated triage 경로로 떨어뜨립니다.
  - `tests/test_watcher_core.py:2758` `test_fresh_slice_ambiguity_operator_request_routes_to_codex_followup`와 `tests/test_watcher_core.py:2793` `test_next_slice_alias_operator_request_stays_gated`이 신규 회귀로 추가되어 있습니다.
  - `tests/test_pipeline_runtime_supervisor.py:2495` `test_write_status_gates_slice_ambiguity_operator_stop_for_24h`와 `tests/test_pipeline_runtime_supervisor.py:2553` `test_write_status_normalizes_next_slice_aliases_to_gated_operator_stop`도 신규 회귀로 들어가 있습니다.
  - `.pipeline/README.md:171`에 `OPERATOR_POLICY: stop_until_exact_slice_selected` → `gate_24h`, `REASON_CODE: gemini_axis_switch_without_exact_slice` → `slice_ambiguity` compatibility 정규화가 짧게 명시되어 있습니다.
  - `.pipeline/operator_request.md`(seq 363)는 line 3 `REASON_CODE: slice_ambiguity`, line 4 `OPERATOR_POLICY: gate_24h`로 canonical 값으로 live unstick 되어 있습니다.
- focused rerun이 모두 통과했습니다.
  - `python3 -m unittest -v tests.test_watcher_core.TurnResolutionTest.test_fresh_slice_ambiguity_operator_request_routes_to_codex_followup tests.test_watcher_core.TurnResolutionTest.test_next_slice_alias_operator_request_stays_gated tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_slice_ambiguity_operator_stop_for_24h tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_normalizes_next_slice_aliases_to_gated_operator_stop` → `Ran 4 tests`, `OK`
  - `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py` → 출력 없음, exit `0`
  - `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md .pipeline/operator_request.md` → 출력 없음, exit `0`
- live runtime status 주장(`autonomy.mode=triage`, `compat.turn_state=CODEX_FOLLOWUP`, `Claude state=WORKING(note=followup)`)은 `/work`가 기록한 시점의 status.json snapshot 진술입니다. 본 verify 시점에는 그 동일 run snapshot을 새로 캡처하지 않았고, 대신 alias 정규화 코드/회귀가 truthful하다는 근거에서 그 snapshot 진술을 신뢰했습니다.

## 검증
- 직접 코드/테스트 대조
  - 대상: `pipeline_runtime/operator_autonomy.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_runtime_supervisor.py`, `.pipeline/README.md`, `.pipeline/operator_request.md`.
  - 결과: alias map(reason-code/policy), `slice_ambiguity` 분류, 4개 신규 회귀, README 한 문장, operator_request canonical 값이 모두 현재 tree와 일치함을 확인했습니다.
- `python3 -m unittest -v tests.test_watcher_core.TurnResolutionTest.test_fresh_slice_ambiguity_operator_request_routes_to_codex_followup tests.test_watcher_core.TurnResolutionTest.test_next_slice_alias_operator_request_stays_gated tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_slice_ambiguity_operator_stop_for_24h tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_normalizes_next_slice_aliases_to_gated_operator_stop`
  - 결과: `Ran 4 tests`, `OK`
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit `0`
- `git diff --check`(scope files): 출력 없음, exit `0`
- broader `tests.test_watcher_core` 전체 135 test 묶음, Playwright, `make e2e-test`은 이번 verify에서 다시 돌리지 않았습니다.
  - 이유: 이번 라운드는 runtime control 분류 한정 alias 정규화이고 watcher state-writer/launcher 같은 broad runtime contract를 바꾸지 않았습니다. focused 4-test 회귀 + py_compile + diff-check가 현재 truth 판정에 충분했습니다. `/work` 자체가 broad 135-test 묶음이 이미 통과했음을 기록한 점도 신뢰 근거입니다.

## 남은 리스크
- alias 정규화는 이번에 실제로 관찰된 `gemini_axis_switch_without_exact_slice` / `stop_until_exact_slice_selected*` wording에 한정됩니다. 같은 fallback family에서 또 다른 비정형 wording이 생기면 다시 false hard stop이 날 수 있습니다.
- live unstick은 `.pipeline/operator_request.md` seq 363 자체를 canonical 값으로 다시 쓴 결과입니다. 이건 hard stop 해제이지 next-slice 결정이 아닙니다. seq 363이 묻고 있던 `Milestone 4 exact slice` 자체는 그 뒤 seq 366 / 369 / (seq 372 pending) CONFLICT family 라운드들이 부분적으로만 답하고 있는 상태입니다.
- broad `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` failure는 이번 라운드 범위 밖이고 별도 truth-sync 라운드 몫으로 dirty state에 남아 있습니다.
- 현재 `.pipeline/claude_handoff.md` seq 372(`Claim Coverage Summary CONFLICT — full browser-visible chain`)는 실제 implement 대기 상태입니다. 이번 verify는 그 슬라이스를 닫지 않았고, alias-gate-recovery는 그 슬라이스 우선순위를 바꾸지 않습니다.
