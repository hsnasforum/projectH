## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `e2e/README.md`
- `.agents/skills/e2e-smoke-triage/SKILL.md`
- `.claude/skills/e2e-smoke-triage/SKILL.md`

## 사용 skill
- `e2e-smoke-triage`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 corrected-save bridge copy와 snapshot contract는 focused unittest로만 검증되어 있었고, 실제 브라우저 상호작용 수준의 Playwright smoke가 비어 있었습니다.
- smoke 시나리오 수와 설명도 `README.md`, `e2e/README.md`, acceptance 계열 문서 사이에 드리프트가 있어, 실제 실행 기준으로 다시 맞출 필요가 있었습니다.

## 핵심 변경
- corrected-save first bridge path를 검증하는 Playwright smoke 1개를 추가했습니다.
- 새 smoke는 correction area 초기 disabled helper 상태, `수정본 기록` 이후 bridge enable, recorded correction 기반 bridge approval 생성, request-time frozen preview 유지, approval 후 corrected-save 실제 저장까지 한 경로로 검증합니다.
- bridge approval 이후 textarea를 다시 수정해도 기존 pending approval preview가 auto-rebase 되지 않는다는 점과, 실제 저장 본문이 original draft가 아니라 bridge 시점 recorded correction 기준이라는 점을 브라우저에서 확인하도록 했습니다.
- 앱 코드나 selector/copy는 추가 수정하지 않았습니다. 기존 `data-testid`와 helper wording만으로 시나리오를 안정적으로 검증할 수 있음을 확인했습니다.
- smoke count와 시나리오 설명을 현재 실제 기준으로 문서에 동기화했습니다. 브라우저 smoke는 이제 총 7개 시나리오를 명시하며, corrected-save first bridge path를 포함합니다.
- repo-specific smoke coverage 설명을 따라 `.agents/skills/e2e-smoke-triage/SKILL.md`와 `.claude/skills/e2e-smoke-triage/SKILL.md`도 같은 범위로 맞췄습니다.

## 검증
- 실행함: `make e2e-test`
- 실행함: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행함: `python3 -m py_compile app/web.py tests/test_smoke.py tests/test_web_app.py`
- 실행함: `git diff --check`
- 실행함: `rg -n "response-correction-save-request|corrected_text|save_content_source|source_message_id|preview_markdown|snapshot|수정본 기록|저장 요청" e2e/tests/web-smoke.spec.mjs app/templates/index.html app/web.py tests/test_smoke.py tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/README.md`
- 결과:
- `make e2e-test`: `7 passed (56.0s)`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`: `Ran 138 tests ... OK`
- `git diff --check`: 통과

## 남은 리스크
- 이번 라운드에서 해소한 리스크:
- corrected-save first bridge path가 실제 브라우저 상호작용 수준에서도 disabled-helper, recorded-correction-only bridge, immutable snapshot, corrected-save write까지 동작함을 확인했습니다.
- smoke count와 scenario 설명 드리프트를 현재 구현 기준으로 문서에 맞췄습니다.
- 여전히 남은 리스크:
- corrected-save는 첫 bridge 경로만 Playwright smoke로 커버합니다. reissue, overwrite edge, stale snapshot 차이 표시 같은 더 넓은 조합은 여전히 focused unittest 중심입니다.
- approval card는 snapshot 불변 계약을 wording으로는 드러내지만, pending snapshot과 최신 recorded correction의 차이를 별도 읽기 전용 indicator로 보여 주지는 않습니다.
