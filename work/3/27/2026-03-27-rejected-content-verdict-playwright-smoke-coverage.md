# 2026-03-27 rejected content verdict Playwright smoke coverage

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `e2e/README.md`
- `work/3/27/2026-03-27-rejected-content-verdict-playwright-smoke-coverage.md`

## 사용 skill
- `e2e-smoke-triage`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서는 shipped `내용 거절` content-verdict path가 구현과 focused unittest로는 고정됐지만, 실제 브라우저 상호작용 수준의 Playwright smoke는 비어 있었습니다.
- 특히 response-card action placement, no-approval-cancel semantics, later explicit save supersession이 브라우저에서 아직 검증되지 않아, 현재 shipped contract를 smoke baseline에 올릴 필요가 있었습니다.
- smoke count와 next-step 문구도 아직 `내용 거절` browser coverage 이전 상태를 가리키고 있어, 실제 실행 기준으로 문서를 다시 맞춰야 했습니다.

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs`에 dedicated reject smoke 1개를 추가했습니다.
- 새 smoke는 한 시나리오 안에서 아래를 검증합니다:
  - grounded-brief 응답과 pending save approval가 동시에 열린 상태
  - `내용 거절` action이 response card에 있고 approval box 안에는 없다는 점
  - `내용 거절` 실행 후 `rejected` meta가 반영되지만 기존 approval preview와 경로 입력이 그대로 유지된다는 점
  - 같은 approval를 나중에 승인하면 실제 note 저장이 성공하고, content verdict state가 latest explicit save 기준으로 supersede 된다는 점
- 앱 코드나 selector/copy는 추가 수정하지 않았습니다. 기존 `data-testid`, helper copy, saved-path/meta surface만으로 시나리오를 안정적으로 확인할 수 있음을 확인했습니다.
- smoke count와 설명을 문서에 동기화했습니다:
  - Playwright smoke는 이제 총 8개 시나리오입니다.
  - corrected-save first bridge path와 `내용 거절` content-verdict path가 모두 shipped browser baseline으로 명시됩니다.
  - roadmap 문구는 “reject smoke를 추가한다”에서 “현재 reject surface를 작게 유지하고, later reject-note UX만 별도 truthfully 확장한다”로 갱신했습니다.

## 검증
- 실행함: `cd /home/xpdlqj/code/projectH/e2e && npx playwright test --grep "내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다"`
- 실행함: `python3 -m py_compile app/web.py tests/test_smoke.py tests/test_web_app.py`
- 실행함: `rg -n "내용 거절|rejected|content_reject|explicit_content_rejection|corrected_outcome|content_reason_record" e2e/tests/web-smoke.spec.mjs app/templates/index.html app/web.py tests/test_smoke.py tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/README.md`
- 실행함: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행함: `make e2e-test`
- 실행함: `git diff --check`
- 결과:
  - targeted Playwright: `1 passed (14.3s)`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`: `Ran 141 tests in 1.904s`
  - `make e2e-test`: `8 passed (1.1m)`
  - `git diff --check`: 통과

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크였던 “shipped `내용 거절` path가 아직 Playwright smoke에 올라가 있지 않다”는 이번 라운드에서 해소했습니다.
- 이번 라운드에서 함께 해소한 리스크는 smoke count / scenario 설명 드리프트였습니다. README, acceptance, milestones, backlog, next-steps, e2e README가 이제 실제 8개 browser scenario를 가리킵니다.
- 여전히 남은 리스크는 더 긴 히스토리 조합입니다:
  - late flip after explicit original-draft save는 현재 browser smoke에 별도 시나리오로 풀어 놓지 않았습니다.
  - explicit correction-submit supersession은 여전히 focused unittest 중심입니다.
  - reject note UX와 richer reject labels는 아직 truthful input surface가 없으므로 구현하지 않았습니다.
