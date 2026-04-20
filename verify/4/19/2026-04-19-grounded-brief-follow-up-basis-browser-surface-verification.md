# 2026-04-19 grounded-brief follow-up basis browser surface verification

## 변경 파일
- `verify/4/19/2026-04-19-grounded-brief-follow-up-basis-browser-surface-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/19/2026-04-19-grounded-brief-follow-up-basis-browser-surface.md`가 grounded-brief correction submit 이후 같은 세션 follow-up / re-summary basis를 브라우저에서 분명히 보이게 했다고 주장하므로, 실제 코드/문서/브라우저 smoke가 그 설명과 맞는지 다시 확인해야 했습니다.
- prompt에 적힌 `VERIFY` 경로 `verify/4/19/2026-04-19-codex-dispatch-double-paste-guard-verification.md`는 earlier watcher-family verify라서 덮어쓰지 않았습니다. 이번 grounded-brief browser round는 별도 `/verify` note로 닫는 편이 truth 보존에 맞습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `app/static/app.js::updateCorrectionHelperText()`는 세 분기 모두에서 follow-up basis 문구를 실제로 추가했습니다.
    - 미기록 상태: `아직 기록된 수정본이 없어 같은 세션의 후속 질문과 재요약은 원본 요약 기준으로 이어집니다.`
    - 기록본 유지 상태: `기록된 수정본이 같은 세션의 후속 질문과 재요약 기준이 됩니다.`
    - 기록 후 입력창 재변경 상태: `후속 질문과 재요약도 직전 기록본 기준으로 이어지며, 입력창의 새 변경을 기준으로 바꾸려면 다시 수정본 기록을 눌러 주세요.`
  - `app/static/app.js::renderContext()`는 `active_context.summary_hint`를 더 이상 raw block으로만 찍지 않고, `후속 질문 / 재요약 기준 (기록된 수정본):` 또는 `후속 질문 / 재요약 기준 (현재 요약):` 라벨과 함께 렌더링합니다.
  - `e2e/tests/web-smoke.spec.mjs`에는 새 scenario `corrected follow-up basis는 기록된 수정본을 같은 세션의 후속 질문 / 재요약 기준으로 노출합니다`가 실제로 추가돼 있고, 기존 corrected-save smoke들의 기대 문자열도 새 follow-up-basis copy에 맞게 갱신돼 있습니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`도 같은 browser-visible contract를 실제로 적고 있습니다.
- focused rerun도 `/work`의 검증 주장과 맞았습니다.
  - `python3 -m unittest -v tests.test_smoke.SmokeTest.test_correction_updates_active_context_summary_hint` 통과
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "corrected.*follow-up basis|follow-up basis.*corrected|수정본.*후속" --reporter=line`은 `1 passed (10.7s)`
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "corrected-save" --reporter=line`은 `2 passed (37.0s)`
  - `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`는 출력 없이 통과
- 다만 file-isolated cleanliness는 아닙니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`에는 current tree 기준 다른 family의 controller/runtime dirty hunks도 함께 존재합니다.
  - 이번 grounded-brief follow-up-basis 관련 hunks 자체는 실제로 들어가 있고 code truth와도 맞지만, 해당 문서 파일들이 이번 round 전용 변경만 담고 있는 상태는 아닙니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `app/static/app.js`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `work/4/19/2026-04-19-grounded-brief-follow-up-basis-browser-surface.md`
  - 결과: `/work`가 설명한 grounded-brief correction helper copy, context-box basis label, focused Playwright scenario, docs sync가 현재 tree와 일치함을 확인했습니다.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_correction_updates_active_context_summary_hint`
  - 결과: `Ran 1 test`, `OK`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "corrected.*follow-up basis|follow-up basis.*corrected|수정본.*후속" --reporter=line`
  - 결과: `1 passed (10.7s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "corrected-save" --reporter=line`
  - 결과: `2 passed (37.0s)`
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 출력 없음, exit code `0`
- verify 중 처음에 Playwright 두 명령을 병렬로 띄웠을 때는 local webServer port 충돌로 두 번째 실행이 `Address already in use`로 실패했습니다.
  - 이후 같은 두 suite를 순차로 다시 실행했고 모두 통과했습니다.
  - 따라서 이 실패는 구현 회귀라기보다 verify 실행 방식의 포트 충돌이었습니다.
- full browser suite나 broader Python suite는 이번 verify에서 다시 실행하지 않았습니다.
  - 이유: latest `/work`의 핵심 수정은 grounded-brief correction/browser contract와 그 focused smoke 경계였고, isolated rerun만으로도 current truth 판정에 충분했습니다.

## 남은 리스크
- 현재 browser label owner는 아직 완전히 안정적이지 않습니다.
  - `app/static/app.js::compactSummaryHintForBasis()`가 store-side `summary_hint` compact 규칙(whitespace normalize + 240자 cap)을 브라우저에서 다시 복제해 `기록된 수정본` 여부를 추론합니다.
  - storage나 localization 규칙이 바뀌면 follow-up basis label만 `(현재 요약)`으로 잘못 떨어질 수 있습니다.
- 이번 round의 browser smoke는 helper copy와 context-box basis surface는 직접 고정했지만, correction 이후 실제 composer follow-up 한 번을 보내서 visible answer가 recorded correction basis로 이어지는지까지는 아직 browser path에서 닫지 않았습니다.
- current tree에는 watcher/runtime/controller/browser/docs 쪽 broad dirty worktree가 계속 남아 있으므로, 다음 round도 unrelated hunks를 revert하지 않고 grounded-brief active-context family로만 bounded하게 움직여야 합니다.
