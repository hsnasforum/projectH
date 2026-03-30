# 2026-03-28 mock smoke baseline candidate confirmation

## 변경 파일
- `e2e/playwright.config.mjs`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `e2e/README.md`
- `work/3/28/2026-03-28-mock-smoke-baseline-candidate-confirmation.md`

## 사용 skill
- `e2e-smoke-triage`: Playwright smoke 실패 원인을 `mock` baseline 계약, 세션 준비 레이스, candidate confirmation assertion drift로 나눠 최소 수정 순서로 정리했습니다.
- `approval-flow-audit`: candidate confirmation이 approval-backed save와 섞이지 않고 response-card 바깥 approval surface와 분리된 채 유지되는지 확인했습니다.
- `doc-sync`: `mock` smoke baseline 계약과 candidate confirmation browser coverage 설명을 README / acceptance / milestone / backlog / next-steps / e2e README에 구현 truth로 맞췄습니다.
- `release-check`: 실제 실행한 `make e2e-test`, `LOCAL_AI_MODEL_PROVIDER=ollama ... make e2e-test`, focused unittest, `py_compile`, `git diff --check`, `rg` 결과만 기준으로 마감 검증을 정리했습니다.
- `work-log-closeout`: 이번 검증/구현 round의 변경 파일, 실행 검증, 남은 리스크를 `/work` 형식으로 남겼습니다.

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 브라우저 smoke가 stable `mock` baseline을 truthful하게 강제하지 못할 수 있다는 점과, candidate confirmation browser path가 flaky한 세션/UI 상태에 기대고 있다는 점이었습니다.
- 이번 라운드의 목적은 shipped candidate confirmation semantics를 넓히지 않고, Playwright smoke를 다시 신뢰 가능한 회귀 기준으로 복구하는 것이었습니다.

## 핵심 변경
- `e2e/playwright.config.mjs`에서 smoke webServer를 dedicated `mock` baseline으로 고정했습니다.
  - inherited `LOCAL_AI_MODEL_PROVIDER` / `LOCAL_AI_OLLAMA_MODEL` 값을 먼저 비우고
  - `LOCAL_AI_MODEL_PROVIDER=mock`를 다시 강제하며
  - `reuseExistingServer: false`로 smoke 포트의 기존 서버 재사용을 끊었습니다.
- `e2e/tests/web-smoke.spec.mjs`의 세션 준비를 안정화했습니다.
  - 페이지 초기 bootstrap fetch가 끝난 뒤 시작하도록 `networkidle`을 기다리고
  - 각 시나리오가 `새 세션`으로 기존 approval UI를 비운 뒤 자체 session id를 사용하도록 바꿨습니다.
- candidate confirmation browser smoke는 기존 시나리오를 유지하되 same source message 추적으로 강화했습니다.
  - explicit correction 후 `session_local_candidate` 발생
  - response-card의 `이 수정 방향 재사용 확인` action 노출
  - corrected-save approval 이후에도 save support와 별도 trace 유지
  - same source message의 `candidate_confirmation_record` 기록
  - later correction 이후 current state에서 stale confirmation clear
  - `session_local_candidate`에는 여전히 `has_explicit_confirmation`, `promotion_basis`, `promotion_eligibility`, `durable_candidate`를 추가하지 않음을 브라우저에서 확인했습니다.
- smoke 문서를 모두 현재 계약으로 동기화했습니다.
  - smoke count는 11로 유지
  - `mock` dedicated no-reuse launch contract
  - candidate confirmation scenario가 same source message / save support separation / stale clear를 확인한다는 설명을 맞췄습니다.

## 검증
- 실행함: `make e2e-test`
  - `11 passed (2.0m)`
- 실행함: `LOCAL_AI_MODEL_PROVIDER=ollama LOCAL_AI_OLLAMA_MODEL=llama3.2 make e2e-test`
  - `11 passed (2.0m)`
- 실행함: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 159 tests in 2.222s`
  - `OK`
- 실행함: `python3 -m py_compile storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행함: `git diff --check`
- 실행함: `rg -n "candidate_confirmation_record|explicit_reuse_confirmation|session_local_candidate|mock provider|LOCAL_AI_MODEL_PROVIDER|response-box|reuseExistingServer" e2e/playwright.config.mjs e2e/tests/web-smoke.spec.mjs app/templates/index.html app/web.py tests/test_smoke.py tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/README.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 “smoke baseline이 live runtime이나 stale browser session에 흔들릴 수 있다”는 리스크는 이번 라운드에서 dedicated mock webServer + no-reuse + test-session isolation으로 줄였습니다.
- 이전 closeout에서 남아 있던 “candidate confirmation browser path가 직접 회귀를 주지 못한다”는 리스크도 same source message anchored smoke assertion으로 줄였습니다.
- 여전히 남은 리스크는 real `ollama` browser path가 smoke default가 아니라 optional/manual 확인 대상이라는 점입니다.
- future `durable_candidate` projection, review queue, user-level memory는 이번 라운드에서도 열지 않았고, shipped `session_local_candidate` / `candidate_confirmation_record` semantics는 그대로 유지했습니다.
