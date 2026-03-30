## 변경 파일
- `app/templates/index.html`
- `e2e/tests/web-smoke.spec.mjs`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `e2e/README.md`

## 사용 skill
- `e2e-smoke-triage`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 남은 리스크는 "이미 원문 저장이 끝난 뒤 나중에 `내용 거절`을 눌렀을 때 saved history와 latest content verdict가 브라우저에서 truthfully 분리되어 읽히는지"가 Playwright baseline으로 아직 고정되지 않았다는 점이었습니다.
- 이번 라운드는 그 late history path를 별도 browser smoke로 올리고, 필요 최소한의 wording만 보강해 현재 shipped contract를 브라우저 기준으로 고정하기 위한 작업이었습니다.

## 핵심 변경
- Playwright smoke에 `원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다` 시나리오를 추가했습니다.
- 이 시나리오는 original-draft save 완료 후 같은 source message에 `내용 거절`을 눌렀을 때:
  - 저장된 note와 saved path는 그대로 유지되고
  - latest content verdict만 `rejected`로 바뀌며
  - 저장 본문이 자동으로 덮어써지지 않는다는 점을 브라우저와 실제 파일 본문 기준으로 함께 확인합니다.
- response-card wording은 최소 범위로만 보강했습니다.
  - late reject notice: 이미 저장된 note는 그대로 유지되고 latest verdict만 바뀐다고 알립니다.
  - content-verdict helper: 이미 저장된 note/path는 유지되고 이번 `내용 거절`은 최신 판정만 바꾼다고 알립니다.
- focused service regression을 1개 추가해 original-draft save 이후 late reject가 saved history를 지우지 않는 현재 계약을 고정했습니다.
- smoke 문서는 실제 기준 9개 시나리오로 동기화했고, late-flip scenario 설명을 README / acceptance / milestone / backlog / next-steps / e2e README / spec / architecture에 반영했습니다.

## 검증
- `python3 -m py_compile app/web.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 145 tests in 1.831s`
  - `OK`
- `make e2e-test`
  - `9 passed (1.3m)`
- `rg -n "내용 거절|거절 메모 기록|rejected|content_reason_record|latest content verdict|저장했습니다|원문 저장 승인" e2e/tests/web-smoke.spec.mjs app/templates/index.html app/web.py tests/test_smoke.py tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/README.md`
- `git diff --check`

## 남은 리스크
- 이번 라운드로 late flip after explicit original-draft save는 브라우저 baseline으로 고정됐습니다.
- 아직 남은 리스크는 manual blank-note clear UX와 richer reject labels처럼 reject-note surface를 넓히는 후속 판단입니다.
- 또 하나의 남은 질문은 corrected-save 저장 이후 다시 late reject / re-correct가 반복되는 더 긴 history chain을 별도 browser scenario로 올릴지 여부입니다.
