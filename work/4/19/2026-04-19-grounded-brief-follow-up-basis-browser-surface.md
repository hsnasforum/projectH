# 2026-04-19 grounded-brief follow-up basis browser surface

## 변경 파일
- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/19/2026-04-19-grounded-brief-follow-up-basis-browser-surface.md`

## 사용 skill
- `doc-sync`: 이번 browser-visible contract 변경을 README / PRODUCT_SPEC / ACCEPTANCE_CRITERIA와 좁게 동기화하기 위해 사용했습니다.
- `work-log-closeout`: 이번 grounded-brief 수정본-follow-up-basis 라운드의 `/work` closeout을 repo 규약 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- shipped docs는 이미 correction submit이 `active_context.summary_hint`를 갱신하고, 같은 세션의 후속 질문 / 재요약이 수정본을 기준으로 이어진다고 적고 있습니다.
- 그러나 브라우저 표면은 이 계약을 분명하게 드러내지 않았습니다. 기록된 수정본이 저장 승인 흐름과 분리된다는 설명만 있었고, follow-up / 재요약 기준이 실제로 바뀐다는 점은 노출되지 않았으며, `#context-text`는 `active_context.summary_hint`를 라벨 없는 raw block으로 출력하고 있었습니다.
- Gemini advice도 이번 라운드에서 watcher/runtime family를 닫고 document-first MVP grounded-brief 축으로 돌아가라고 권고했습니다.
- 이번 라운드는 이 축을 실제 사용자 surface까지 연결하는 bounded slice로 잡았습니다.

## 핵심 변경
- `app/static/app.js::updateCorrectionHelperText()`에 follow-up-basis 문장을 각 분기에 맞게 추가했습니다:
  - 기록된 수정본 없음 → `아직 기록된 수정본이 없어 같은 세션의 후속 질문과 재요약은 원본 요약 기준으로 이어집니다.`
  - 기록된 수정본 있음 + 입력창 변경 없음 → `기록된 수정본이 같은 세션의 후속 질문과 재요약 기준이 됩니다.`
  - 기록된 수정본 있음 + 입력창 변경 있음 → `후속 질문과 재요약도 직전 기록본 기준으로 이어지며, 입력창의 새 변경을 기준으로 바꾸려면 다시 수정본 기록을 눌러 주세요.`
  - 기존 corrected-save 스냅샷 경고는 그대로 유지했습니다.
- `app/static/app.js::renderContext()`가 `active_context.summary_hint` 블록을 빈 줄 하나 뒤에 `후속 질문 / 재요약 기준 (기록된 수정본):` 또는 `후속 질문 / 재요약 기준 (현재 요약):` 라벨과 함께 출력하도록 바꿨습니다.
  - 비교는 새 helper `compactSummaryHintForBasis()`로 수행해, storage-side `" ".join(text.split())` + 240자 잘라내기 규칙과 동일하게 정규화한 최신 `state.latestCorrectionRecordedText`가 현재 `summary_hint`와 일치할 때 "기록된 수정본" 라벨을 붙입니다.
  - 데이터 소스는 기존 `active_context.summary_hint` 그대로이며, 새 필드나 persistence 레이어를 추가하지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`:
  - 기존 corrected-save first-bridge / corrected-long-history 테스트의 `#response-correction-status` 기대 문자열을 새 follow-up-basis 문장을 포함하도록 갱신했습니다.
  - 새 scenario `corrected follow-up basis는 기록된 수정본을 같은 세션의 후속 질문 / 재요약 기준으로 노출합니다`를 추가해, 미기록 상태에서는 `(현재 요약):` 라벨과 원본 요약 문구가 보이고, `수정본 기록` 뒤에는 `(기록된 수정본):` 라벨과 수정본 본문이 `#context-text`에 나타나며 helper copy도 follow-up-basis 계약에 맞게 바뀌는지 직접 고정했습니다.
- `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`를 이번 browser-visible 계약에 맞게 좁게 갱신했습니다. memory scope나 durable cross-session 재사용은 손대지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_correction_updates_active_context_summary_hint`
  - 결과: `Ran 1 test`, `OK`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "corrected.*follow-up basis|follow-up basis.*corrected|수정본.*후속" --reporter=line`
  - 결과: `1 passed (12.3s)`
- `npx playwright test tests/web-smoke.spec.mjs -g "corrected-save" --reporter=line` (문구 갱신으로 깨지지 않았는지 확인)
  - 결과: `2 passed (37.2s)`
- `git diff --check -- app/static/app.js app/templates/index.html e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 출력 없음, exit code `0`
- 이번 라운드는 Milestone 5 grounded-brief browser contract pinning이라 `make e2e-test` full suite는 과하다고 판단해 좁은 Playwright 재실행만 했습니다.

## 남은 리스크
- 이번 라운드는 browser-visible clarity를 좁게 개선한 것입니다. 실제 `active_context.summary_hint`가 수정본으로 갱신되는 storage/agent 계약 자체는 이미 shipped였고 이번 라운드에서 바꾸지 않았습니다. durable cross-session 재사용, 새 storage field, memory scope 확대는 포함되지 않습니다.
- `compactSummaryHintForBasis` 비교는 240자 cap + whitespace 정규화까지만 재현합니다. storage가 추후 compact 규칙을 바꾸면 "(기록된 수정본)" 라벨이 "(현재 요약)"으로 잘못 떨어질 수 있습니다. 이 경우 storage 쪽 규칙과 다시 맞춰야 합니다.
- current tree에는 watcher/runtime/controller/cozy/docs 쪽 unrelated dirty worktree가 계속 많이 남아 있으므로, 다음 리뷰/커밋 시에는 이번 슬라이스 대상 파일(`app/static/app.js`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, 이 `/work` 파일)만 분리해서 보는 편이 안전합니다.
