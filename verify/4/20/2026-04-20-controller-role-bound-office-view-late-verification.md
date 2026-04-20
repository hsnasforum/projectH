# 2026-04-20 controller role-bound office view late verification

## 변경 파일
- `verify/4/20/2026-04-20-controller-role-bound-office-view-late-verification.md`

## 사용 skill
- `round-handoff`: dispatcher가 이번 라운드에 가리킨 `/work`(`work/4/19/2026-04-19-controller-role-bound-office-view.md`)와 mismatch된 verify pointer(`verify/4/19/2026-04-19-response-body-conflict-header-verification.md`)를 실제 tree 상태와 교차 확인하고, 같은 날 기존 verify 노트들을 덮지 않도록 오늘(2026-04-20) 폴더에 별도 late-verification 노트로 남겼습니다.

## 변경 이유
- dispatcher는 오래된 4/19 `/work`인 controller role-bound office view 라운드를 지정했고, 함께 묶인 verify path는 실제로는 다른 family(`response-body-conflict-header`)용이라 /work–verify pair 매칭이 mismatch였습니다. 4/19 verify 폴더에도 `controller-role-bound-office-view` 전용 verify 노트는 없었고, 가장 근접한 것은 `verify/4/19/2026-04-19-watcher-role-bound-turn-state-surface-verification.md`로, 그 노트는 3연속 runtime-hardening 라운드 shipped 상태만 간접적으로 언급했습니다.
- 따라서 이 라운드는 (a) 해당 `/work` 주장이 현재 코드/문서 tree와 일치하는지 truthful하게 재확인하고, (b) mismatch된 dispatcher state와 in-flight seq 423 Milestone 4 reinvestigation cap implement handoff가 동시에 존재하는 상황을 다음 control이 올바르게 처리하도록 기록하는 bridge 성격입니다.

## 핵심 변경
- `work/4/19/2026-04-19-controller-role-bound-office-view.md`의 구현 주장과 현재 tree 상태
  - `controller/server.py:64-95` `_runtime_role_metadata()`가 active profile의 `role_owners` / `prompt_owners` / `enabled_lanes`를 실제로 읽어 runtime status payload에 실어주고 있습니다. `_DEFAULT_ROLE_OWNERS`, `_KNOWN_LANE_NAMES` 가드가 ready profile resolution 실패 시 canonical fallback으로 돌아가는 로직도 그대로입니다.
  - `controller/js/cozy.js`에 `role_owners`, `implement`, `verify`, `advisory`, `claude_desk` / `codex_desk` / `gemini_desk` 키워드 합산 39건이 있고, `data.role_owners`를 읽어 desk label/agent home zone을 계산하는 헬퍼(`:113` 기준)가 들어 있습니다.
  - `tests/test_controller_server.py`는 이번 라운드 실행 기준 `Ran 24 tests`, `OK`로 통과했고, runtime status metadata (`role_owners` / `prompt_owners` / `enabled_lanes`) 계약을 유지하는 회귀가 포함되어 있습니다.
  - `README.md:111`에 `"Office View의 desk label과 agent home zone은 /api/runtime/status의 role_owners를 따릅니다. claude_desk / codex_desk / gemini_desk 키는 각각 implement / verify / advisory role anchor 이름일 뿐, Claude / Codex / Gemini의 고정 소유권을 뜻하지 않습니다."` 문장이 실존합니다.
- 이 라운드는 이미 shipped되어 있으며, 이후 다른 라운드(`watcher-role-bound-turn-state-surface` 등)가 같은 runtime-hardening 축에서 병행 전진했습니다. 따라서 새로 implement할 슬라이스가 이 축에서 바로 파생되지 않습니다.
- 동시에 `.pipeline` rolling slot은 다음 상태입니다.
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `423` — Milestone 4 reinvestigation cap widening 4 → 5 슬라이스가 Gemini 422 advice 기반으로 이미 dispatch된 채 in-flight.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `421` — seq 420 shipped 직후 D/E 후보 중재 요청. Gemini 422 advice로 이미 응답됐고 seq 423 handoff로 변환 완료.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `422` — Option D(reinvestigation cap)를 정확히 pin한 응답. seq 423 handoff로 변환 완료.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `363` — 이미 해결된 과거 `summary_hint_basis` 축 질문. 실제로 닫힌 적 없이 새로운 축이 열리며 묵시적으로 우회됨.
- 이 late-verify 자체는 새 코드/문서 편집을 만들지 않으며, 이미 closed-shipped된 controller 라운드를 사후적으로 truthful로 고정하고 dispatcher state를 투명하게 남기는 게 목적입니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `controller/server.py:64-95`, `controller/js/cozy.js`(`role_owners`/`implement`/`verify`/`advisory`/`claude_desk`/`codex_desk`/`gemini_desk` 합산 39건), `tests/test_controller_server.py`(정렬 24 tests), `README.md:111`, 그리고 `.pipeline/claude_handoff.md`/`gemini_request.md`/`gemini_advice.md`/`operator_request.md` 현재 상태.
  - 결과: `/work`가 설명한 runtime metadata 확장, cozy 헬퍼, status 회귀, README Office View 문장이 모두 현재 tree와 일치했습니다.
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 결과: 출력 없음, exit code `0`.
- `node --check controller/js/cozy.js`
  - 결과: 출력 없음, exit code `0`.
- `python3 -m unittest tests.test_controller_server`
  - 결과: `Ran 24 tests in 0.020s`, `OK`.
- `git diff --check -- controller/server.py controller/js/cozy.js tests/test_controller_server.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 출력 없음, exit code `0`.
- Playwright controller smoke, `make e2e-test`, broad `tests.test_web_app`, `tests.test_pipeline_gui_backend`은 이번 late-verify에서 다시 돌리지 않았습니다. 이 `/work`의 browser-visible 계약은 이미 이전 라운드에 확인됐고, 같은 날 다른 family의 verify들이 해당 축의 truthful 상태를 간접 확인한 바 있어 `.claude/rules/browser-e2e.md` 기준으로 focused unittest + py_compile + node --check + git diff --check가 narrowest 적절 범위였습니다.

## 남은 리스크
- 이번 verify는 dispatcher가 mismatch된 `/work`–`/verify` pair로 올드 라운드를 재-dispatch한 상태에서 이뤄졌습니다. 실제로 shipped된 라운드의 truth 판정은 바뀌지 않지만, dispatcher routing 쪽에 stale redispatch 가능성이 남아 있으므로 다음 control은 이 dispatcher 상태 자체를 operator에게 다시 투명하게 알리는 편이 안전합니다.
- seq 423 `.pipeline/claude_handoff.md` Milestone 4 reinvestigation cap widening 슬라이스는 Gemini 422 arbitration을 통해 정확히 pin된 채 in-flight입니다. 이번 late-verify 라운드가 새 seq 424 implement handoff로 이 슬롯을 덮어쓰면 정당한 in-flight work가 소실되므로, 다음 control은 이 슬롯을 preserve해야 합니다.
- seq 363 `.pipeline/operator_request.md`의 과거 `summary_hint_basis` 관련 질문은 이미 자연적으로 우회되어 현재 Milestone 4 축이 진행 중이지만, STATUS/CONTROL_SEQ 자체는 아직 업데이트되지 않은 상태로 남아 있습니다. 이번 next control이 operator_request 축으로 가면 같은 파일을 최신 seq 424 사유로 덮어쓰게 됩니다.
- unrelated `python3 -m unittest tests.test_web_app` 전체 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state 실패는 이번 verify 범위 밖이며 별도 truth-sync 라운드 몫입니다.
- 다음 control은 slice_ambiguity(D/E 선택)처럼 Gemini가 해소 가능한 유형이 아니라, dispatcher routing state와 축 선택 의도를 operator에게 확인해야 하는 truth-sync/decision blocker에 가깝습니다. 따라서 rule 상 `.pipeline/operator_request.md`(seq 424)로 넘기는 편이 맞고, 이 경로에서도 seq 423 implement handoff를 건드리지 않도록 본 verify에 명시적으로 기록해 두었습니다.
