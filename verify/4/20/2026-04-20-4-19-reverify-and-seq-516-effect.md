# 2026-04-20 4-19 reverify and seq 516 truth-sync effect

## 변경 파일
- `verify/4/20/2026-04-20-4-19-reverify-and-seq-516-effect.md` (본 파일)

## 사용 skill
- `round-handoff`: dispatcher가 stale 4/19 pair(`work/4/19/2026-04-19-controller-fetch-failure-dedupe.md` + `verify/4/19/2026-04-19-operator-stop-verified-blocker-recovery-scope-late-verification.md`)를 다시 re-dispatch한 상태에서, 두 4/19 slice 주장이 current tree에서도 유효한지 narrow-rerun하고 동시에 직전 라운드에서 쓴 `.pipeline/operator_request.md` seq 516 truth-sync 결과를 같이 대조해 next control outcome을 준비했습니다.

## 변경 이유
- dispatcher가 오늘(2026-04-20) WORK로 `work/4/19/2026-04-19-controller-fetch-failure-dedupe.md`를, VERIFY로 sibling `verify/4/19/2026-04-19-operator-stop-verified-blocker-recovery-scope-late-verification.md`를 가리켰습니다. 두 4/19 slice는 서로 다른 축(controller Quest Log dedupe vs. verified-blocker self-heal narrowing)이라 pair mismatch 상태였고, 둘 다 이미 shipped로 truth-closed였습니다.
- 같은 round에서 직전에 `.pipeline/operator_request.md`를 seq 462(stale `advice_g5_not_bounded_first_sub_slice`)에서 seq 516(canonical `waiting_next_control` / `internal_only` / `next_slice_selection`)로 truth-sync 했기 때문에, 이 쓰기가 실제 `test_live_operator_request_header_canonical` skip 동작을 바꿨는지 직접 확인이 필요했습니다.
- `/verify` README의 "pane 안 reasoning만 남기거나 next control slot만 먼저 갱신하는 것은 canonical verification closeout이 아닙니다. `/verify`를 먼저 남기거나 갱신한 뒤에만 다음 control slot을 쓰는 편이 맞습니다" 규칙을 따르려면 seq 517 쓰기 전 verify note가 먼저 필요합니다.

## 핵심 변경
- **4/19 `controller-fetch-failure-dedupe` 주장이 current tree에서도 유지됨**:
  - `controller/js/cozy.js:2921` `function recordStatusFetchFailure(error)`, `:2929` `function clearStatusFetchFailure()`, `:3352` `clearStatusFetchFailure()` 복구 경로 호출, `:3361` `recordStatusFetchFailure(error)` 실패 경로 호출 모두 존재.
  - `controller/js/cozy.js:2926` `pushEvent('err', \`상태 조회 실패: ${message}\`)`, `:2934` `pushEvent('ok', \`상태 조회 복구: ${message}\`)` 리터럴 유지.
  - `e2e/tests/controller-smoke.spec.mjs:101` `test("controller deduplicates repeated status fetch failures and logs one recovery", async ({` 시나리오 존재.
  - `tests.test_controller_server` 실제 재실행: `Ran 24 tests in 0.041s`, `OK`. 4/19 `/work` 기록은 23이었고 그 뒤 1건 추가된 상태지만 모두 green.
- **4/19 `operator-stop-verified-blocker-recovery-scope-late-verification` 주장도 유지됨**:
  - `pipeline_runtime/operator_autonomy.py:178` `def allows_verified_blocker_auto_recovery(control_meta: Mapping[str, Any] | None = None) -> bool` 존재. 4/19 late-verify의 `:168` 인용은 라인 드리프트(+10)일 뿐 함수 자체는 동일.
  - `watcher_core.py:62` import, `:2041` `if not allows_verified_blocker_auto_recovery(control_meta):` 호출 유지.
  - `pipeline_runtime/supervisor.py:22` import, `:434` 같은 guard 호출 유지.
  - watcher/supervisor 두 경계가 여전히 같은 helper를 공유하고 있음을 직접 확인했습니다. unit test는 이번 round의 좁은 축과 직접 관련 없어 좁게 재실행하지 않았습니다.
- **seq 516 truth-sync가 advisory test에 의도한 효과를 냈음**:
  - `tests.test_operator_request_schema` 실제 재실행: `Ran 6 tests in 0.001s`, `OK`. 중요: skip=0. 직전 round(`verify/4/20/2026-04-20-operator-request-live-file-option-a-verification.md`)에서는 `OK (skipped=1)`이었고 skip 메시지가 `"Live file drift detected: REASON_CODE='advice_g5_not_bounded_first_sub_slice'"`였습니다.
  - seq 516의 canonical header(`REASON_CODE: waiting_next_control` 등)가 `SUPPORTED_REASON_CODES`에 포함되므로 `test_live_operator_request_header_canonical`의 drift branch가 더 이상 트리거되지 않고, `OPERATOR_POLICY`(`internal_only`)/`DECISION_CLASS`(`next_slice_selection`) assertIn까지 실제로 실행됨을 확인했습니다. option A 설계대로 추가 test 편집 없이 self-heal됐습니다.
- **`.pipeline` rolling slot snapshot (이 verify note 기준)**:
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `513` — 이미 shipped로 소비(4/20 operator-request-live-file-option-a `/work`로 닫힘). 새 handoff 미발행.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `514` — seq 515 advice로 응답된 stale 상태.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `515` — option C 권고, seq 516 operator_request로 소비됨.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `516` — 이번 라운드에서 seq 517로 supersede 대상(pin 보강 목적).
- **dispatcher re-pointing 상태**: 4/19 pair는 다시 informational. today의 active truth는 4/20 `operator-request-live-file-option-a` `/work` + 이번 verify note + seq 516 operator_request입니다.

## 검증
- `python3 -m unittest tests.test_controller_server`
  - 결과: `Ran 24 tests in 0.041s`, `OK`. 4/19 `/work` baseline(23/OK)에서 1 test 추가된 상태, 실패 없음.
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`. 직전 라운드 `OK (skipped=1)` → seq 516 truth-sync 이후 `OK (skipped=0)`으로 전환.
- narrow code/path 확인
  - `rg -n 'recordStatusFetchFailure|clearStatusFetchFailure' controller/js/cozy.js` → 5 hits(`:2921 def`, `:2929 def`, `:3352 clear`, `:3361 record`). `/work` 기대치 일치.
  - `rg -n '상태 조회 복구|상태 조회 실패' controller/js/cozy.js` → 2 hits(`:2926 실패`, `:2934 복구`).
  - `rg -in 'repeated fetch abort|fetch.*recovery|recovery.*fetch' e2e/tests/controller-smoke.spec.mjs` → 1 hit(`:101 repeated status fetch failures`).
  - `rg -n 'allows_verified_blocker_auto_recovery' pipeline_runtime/*.py watcher_core.py` → 5 hits (`:178 def`, supervisor.py `:22 import`/`:434 call`, watcher_core.py `:62 import`/`:2041 call`). 4/19 late-verify의 `:168 def` 인용은 `:178`로 line shift.
- `git diff --check -- .pipeline/operator_request.md controller/js/cozy.js e2e/tests/controller-smoke.spec.mjs tests/test_controller_server.py`
  - 결과: 출력 없음, 통과.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright controller-smoke(4/19 `/work`가 `12 passed` 기록): 이번 round는 controller fetch-failure 계약을 더 건드리지 않았고 grep으로 new scenario 존재 확인으로 충분. browser-visible contract가 이번 4/20 round에서 widen된 바 없음.
  - `make e2e-test`: 이번 round는 `.pipeline/operator_request.md` control slot 쓰기 + `/verify` note 작성이 주 액션이라 brower/웹 suite는 관련 없음.
  - `tests.test_watcher_core`, `tests.test_pipeline_runtime_supervisor` 전체 스위트: 4/19 late-verify가 직접 재실행해 `OK` 확인한 바 있고, 이번 round가 `allows_verified_blocker_auto_recovery` 자체를 편집하지 않음.
  - `python3 -m unittest tests.test_pipeline_gui_backend` 45/OK baseline: 이번 round가 `pipeline_gui/backend.py`를 건드리지 않음.

## 남은 리스크
- **Dispatcher re-pointing drift 지속**: dispatcher가 오늘 또 4/19 stale pair를 WORK/VERIFY로 가리켰습니다. seq 424 `dispatcher_state_truth_sync` 선례와 4/19 late-verify 선례가 이미 있으므로 이 자체는 신규 위험은 아니지만, 자동화가 "newest valid control / newest work+verify" 우선순위를 계속 정확히 평가해야 합니다. seq 517 operator_request에서 이 상태를 명시적으로 기록해 operator가 매번 수동 재조정하지 않게 합니다.
- **seq 516 → seq 517 churn 여부**: seq 516의 canonical literals는 이미 advisory test green을 달성했습니다. seq 517 쓰기의 추가 가치는 (a) 이번 verify note 결과를 `BASED_ON_VERIFY`에 포함해 정보 체인을 최신으로 유지, (b) advisory test skip→green 전환 사실을 `Reason`에 고정, (c) dispatcher re-pointing 관찰을 operator에게 가시화하는 것입니다. 그 외 canonical decision literals는 유지합니다.
- **operator decision 여전히 미결**: G7 family 3라운드 포화 이후 Gemini 515가 G8-pin / G11 / G3 / G7 option B / gate-blocking 어느 것도 tight pin으로 권고할 수 없었던 상태입니다. 다음 operator 응답이 오기 전에는 implement-lane handoff를 열 truthful 근거가 없습니다.
- **오늘(2026-04-20) docs-only round count**: 0 유지. 이번 round는 `.pipeline/operator_request.md` + `/verify` note 두 곳을 편집했고 둘 다 canonical truth-sync / verification 성격이라 docs-only micro-slice 반복 조건에 해당하지 않습니다.
- **runtime gating 미연결**: `normalize_decision_class` / `normalize_reason_code` 여전히 pass-through. 세 literal의 gate/control-writer 강제는 별도 슬라이스로 유지.
- **unrelated red tests**: `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건과 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state 실패 family는 이번 축과 무관해 그대로 남아 있습니다.
- **Dirty worktree**: broad unrelated dirty files가 여전히 많습니다. 이번 round에서 실제 편집한 파일은 `.pipeline/operator_request.md`(직전 turn) + `verify/4/20/2026-04-20-4-19-reverify-and-seq-516-effect.md`(이 파일) + `.pipeline/operator_request.md` seq 517 supersede(다음 쓰기 예정)뿐입니다.
