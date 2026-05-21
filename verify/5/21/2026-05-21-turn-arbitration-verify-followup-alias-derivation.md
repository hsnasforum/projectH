# verify: 2026-05-21 turn arbitration verify-followup alias derivation

## 대상 work

`work/5/21/2026-05-21-turn-arbitration-verify-followup-alias-derivation.md`

## 이전 verify

`verify/5/21/2026-05-21-role-routes-alias-cleanup.md`

## 검증 결과

`VERIFY_DONE`.

최신 `/work`의 핵심 주장인 `pipeline_runtime/turn_arbitration.py`의
`LEGACY_WATCHER_TURN_ALIASES`를 `VERIFY_FOLLOWUP_ROUTE_ALIASES`에서 파생하도록
변경한 점, `LEGACY_CODEX_FOLLOWUP_ROUTE` 직접 import 제거, 그리고
`tests/test_turn_arbitration.py`의 alias set 전체 수렴 테스트 추가는 현재 코드와
재실행 검증 기준으로 사실입니다.

## 사용 skill

- `round-handoff`: 최신 구현 closeout을 코드와 targeted 검증으로 재확인하고
  `/verify` 기록을 남기기 위해 사용했습니다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 operator stop이나 advisory가 아닌
  같은 route family의 좁은 다음 구현 control로 수렴하기 위해 사용했습니다.

## 변경 파일

변경 파일 - 없음. 이 라운드는 검증 및 control 작성 라운드이며 구현 파일은
수정하지 않았습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/21/2026-05-21-turn-arbitration-verify-followup-alias-derivation.md`
- `verify/5/21/2026-05-21-role-routes-alias-cleanup.md`
- `pipeline_runtime/turn_arbitration.py`
- `tests/test_turn_arbitration.py`
- `pipeline_runtime/role_routes.py`
- `tests/test_pipeline_runtime_schema.py`

## 재실행 검증

- `python3 -m py_compile pipeline_runtime/turn_arbitration.py tests/test_turn_arbitration.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_turn_arbitration`
  - 결과: PASS. `Ran 12 tests in 0.001s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.RoleRoutesTest`
  - 결과: PASS. `Ran 2 tests in 0.001s`, `OK`.
- `git diff --check -- pipeline_runtime/turn_arbitration.py tests/test_turn_arbitration.py work/5/21/2026-05-21-turn-arbitration-verify-followup-alias-derivation.md`
  - 결과: PASS, 출력 없음.

## 코드 확인

- `pipeline_runtime/turn_arbitration.py`
  - `VERIFY_FOLLOWUP_ROUTE_ALIASES`를 import합니다.
  - `LEGACY_WATCHER_TURN_ALIASES`는 alias set comprehension으로 구성됩니다.
  - `legacy_watcher_turn_name()`의 기존 출력 shape은 유지됩니다.
- `tests/test_turn_arbitration.py`
  - `test_watcher_turn_name_uses_all_verify_followup_route_aliases`가
    `VERIFY_FOLLOWUP_ROUTE_ALIASES`의 모든 alias를 순회하며
    `legacy_watcher_turn_name(alias) == VERIFY_FOLLOWUP_ROUTE`를 검증합니다.

## 실행하지 않은 검증

- live `claude` 실행, tmux/session access, controller/browser server, Playwright,
  full smoke, long soak는 실행하지 않았습니다.
- 전체 repo unittest discover는 실행하지 않았습니다. 이번 변경은 turn arbitration
  alias derivation과 RouteSpec compatibility에 한정됩니다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지
  않았습니다.

## 런타임 표면

Prompt에 포함된 `RUNTIME_STATUS_AT_DISPATCH`를 권위 있는 dispatcher surface로
사용했습니다.

- `runtime_state: RUNNING`
- `automation_health: recovering`
- `automation_next_action: retrying`
- `active_control: .pipeline/implement_handoff.md#2089 implement`
- `turn_state: IDLE`
- `active_round: VERIFY_PENDING`

lane-local `status --json`, `doctor --json`, `tmux` 확인은 실행하지 않았고, 그
종류의 lane-local access mismatch를 operator boundary 근거로 사용하지 않았습니다.

## 판정

- 최신 `/work`의 구현 주장은 검증 완료입니다.
- operator-only boundary, approval-record repair, truth-sync repair, destructive
  action, commit/push/PR/merge/release boundary는 없습니다.
- advisory가 활성화되어 있지만, 다음 same-family current-risk reduction이
  구체적입니다. `role_routes.py`의 route normalizer들은 아직 개별 legacy 상수
  비교에 의존하므로, 이미 존재하는 `RouteSpec.aliases`를 공유 source로 삼도록
  좁게 정리할 수 있습니다.

## 남은 리스크

- `pipeline_runtime/role_routes.py`의 `normalize_followup_route`,
  `normalize_verify_triage_escalation`, `normalize_verify_triage_reason`은 아직
  각각 특정 legacy 상수 하나를 직접 비교합니다. 현재 alias set이 두 값뿐이라
  동작은 통과하지만, alias family가 확장될 때 같은 drift가 재발할 수 있습니다.
- 현재 worktree에는 이전 Claude print-pipe 계열 dirty 변경과 여러 `/work`,
  `/verify`, `report/gemini` 기록이 남아 있습니다. 이번 라운드에서는
  `turn_arbitration.py`와 직접 테스트 범위만 검증했고, unrelated dirty 변경은
  되돌리거나 포함하지 않았습니다.
- 이번 evidence는 route/turn helper local unit evidence이며 full-smoke pass,
  release-ready, publication-ready 근거가 아닙니다.

## 다음 컨트롤 판단

COUNCIL_DECISION: implement
REASON_CODE: role_route_normalizers_alias_set_derivation
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2090

EVIDENCE:
- `work/5/21/2026-05-21-turn-arbitration-verify-followup-alias-derivation.md`
- `verify/5/21/2026-05-21-turn-arbitration-verify-followup-alias-derivation.md`
- `pipeline_runtime/role_routes.py`
- `pipeline_runtime/turn_arbitration.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_turn_arbitration.py`

REJECTED:
- `.pipeline/operator_request.md`: destructive write, credential/auth,
  approval-record repair, truth-sync repair, merge, release, external
  publication, or immediate safety boundary가 없습니다.
- `.pipeline/advisory_request.md`: 같은 route family 안에서 exact next slice가
  명확합니다. `role_routes` normalizer들을 alias set 기반으로 바꾸고 targeted
  tests로 잠그는 bounded 구현으로 수렴할 수 있습니다.
- commit/push/PR handoff: implement prompt가 commit, push, branch/PR publication,
  PR creation, merge, release를 금지합니다.
