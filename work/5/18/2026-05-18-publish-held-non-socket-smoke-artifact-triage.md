# 2026-05-18 publish held non-socket smoke artifact triage

## 변경 파일

- `controller/js/cozy.js`
- `e2e/tests/web-smoke.spec.mjs`
- `work/5/18/2026-05-18-publish-held-non-socket-smoke-artifact-triage.md`

## 사용 skill

- `e2e-smoke-triage`: Playwright full-smoke 실패 6건을 browser/webServer 재실행 없이 기존 source/test 증거로 분류하는 데 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 정적 검사, 실행하지 않은 browser 검증, 남은 리스크를 `/work` 형식으로 기록하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1930` handoff는 publication held 상태를 유지하면서, Playwright/webServer/socket/tmux/runtime 명령 없이 기존 evidence와 source/test inspection만으로 full-smoke 실패 6건을 좁히라고 지시했습니다.
- `e2e/test-results`에는 `rg --files e2e/test-results` 기준 읽을 artifact가 없어, 실패 지점의 spec과 구현 소스만으로 deterministic한 수정 가능 여부를 판단했습니다.
- 이전 targeted Playwright rerun path는 `local_socket_guard_auto_held`이므로 이번 slice는 browser rerun pass나 release/publication readiness를 주장하지 않습니다.

## 핵심 변경

- `controller/js/cozy.js`에서 `active_round.state`가 `VERIFYING` 또는 `RECEIPT_PENDING`일 때 해당 role owner lane이 snapshot상 `ready`여도 화면 상태를 `working`으로 표시하도록 보정했습니다. `turn_state`만으로는 ready/idle lane을 working으로 올리지 않는 기존 guard는 유지했습니다.
- `e2e/tests/web-smoke.spec.mjs`의 mock summary 기대값을 active preference prefix가 붙은 현재 shipped behavior와 맞췄습니다. `[모의 요약]` 또는 `[모의 요약, 선호 N건 반영]`을 모두 허용하되 요약 본문/approval preview 구조 검증은 유지했습니다.
- `e2e/tests/web-smoke.spec.mjs`의 strict locator ambiguity 두 곳을 좁혔습니다. `수정` 버튼은 title exact regex로, `활성화` 버튼은 해당 preference card 내부로 scope를 제한했습니다.
- production Python code, storage schema, root instruction docs, product docs, prompts, agent rules, pipeline controls는 수정하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication은 수행하지 않았고 publication은 계속 held 상태입니다.

## 검증

- Playwright, `make e2e-test`, local webServer startup, runtime start/stop/restart, socket/tmux 명령은 실행하지 않았습니다. 현재 lane의 targeted Playwright rerun path가 `local_socket_guard_auto_held`이고, handoff가 non-socket inspection/fix로 제한했기 때문입니다.
- `rg --files e2e/test-results`
  - 출력 없음. 기존 Playwright artifact를 찾지 못했습니다.
- `node --check e2e/tests/controller-smoke.spec.mjs`
  - 출력 없이 통과했습니다.
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 출력 없이 통과했습니다.
- `node --check controller/js/cozy.js`
  - 출력 없이 통과했습니다.
- `git diff --check -- e2e/tests/controller-smoke.spec.mjs e2e/tests/web-smoke.spec.mjs controller app core storage work/5/18/2026-05-18-publish-held-non-socket-smoke-artifact-triage.md`
  - 출력 없이 통과했습니다.
- `git diff --no-index --check -- /dev/null work/5/18/2026-05-18-publish-held-non-socket-smoke-artifact-triage.md`
  - 출력 없음. `--no-index` exit code 1은 `/dev/null`과 새 파일의 내용 차이로 발생할 수 있어 whitespace-check pass signal로 해석했습니다.
- `git status --short -- e2e/tests/controller-smoke.spec.mjs e2e/tests/web-smoke.spec.mjs controller app core storage work/5/18/2026-05-18-publish-held-non-socket-smoke-artifact-triage.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - 출력: `M controller/js/cozy.js`, `M e2e/tests/web-smoke.spec.mjs`, `?? work/5/18/2026-05-18-publish-held-non-socket-smoke-artifact-triage.md`
- Python 파일은 변경하지 않았으므로 `python3 -m py_compile`은 실행하지 않았습니다.

## 남은 리스크

- 이번 slice는 browser rerun을 수행하지 않았으므로 full-smoke 6건이 실제 브라우저 환경에서 모두 해소됐다고 주장하지 않습니다.
- `controller/js/cozy.js`의 active-round 표시 보정은 정적 문법 검사만 통과했습니다. socket-capable 환경에서 controller focused smoke 재실행이 필요합니다.
- `e2e/tests/web-smoke.spec.mjs`의 expectation/locator 조정도 정적 문법 검사만 통과했습니다. socket-capable 환경에서 관련 web-smoke focused rerun 또는 full-smoke rerun이 필요합니다.
- publication held 상태가 유지되며, 이 closeout만으로 release-ready, publication-ready, full-smoke-pass readiness를 주장할 수 없습니다.
- dirty tree는 그대로 보존했습니다. stash apply/pop/drop/clear/branch/store/rewrite/discard는 수행하지 않았습니다.
