# 2026-03-31 zero-strong-slot history-card badge Playwright smoke verification

## 변경 파일
- `verify/3/31/2026-03-31-zero-strong-slot-history-card-badge-playwright-smoke-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-zero-strong-slot-history-card-badge-playwright-smoke.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-zero-strong-slot-natural-reload-exact-field-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 zero-strong-slot entity-card의 downgraded verification badge가 browser history-card header에서 과장되지 않음을 Playwright smoke로 잠그는 e2e-only slice라고 적고 있으므로, 이번 검수에서는 해당 smoke hunk 존재 여부, scenario count 유지 여부, docs/service 무변경 주장, 현재 MVP 방향 일탈 여부, 그리고 note가 적은 최소 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 e2e-only 변경 주장은 현재 코드와 일치합니다.
- `e2e/tests/web-smoke.spec.mjs`의 기존 `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다` scenario에 4번째 history card가 실제로 추가되어 있고, `answer_mode = "entity_card"`, `verification_label = "설명형 단일 출처"`, `source_roles = ["백과 기반"]`인 zero-strong-slot 케이스를 검증합니다.
- 새 assertion도 latest `/work` 설명과 맞습니다. 추가된 4번째 card는 answer-mode badge `설명 카드`, verification badge `검증 중` + `ver-medium`, source-role badge `백과 기반(높음)` + `trust-high`를 확인합니다. 즉 strong badge가 아니라 downgraded medium badge로 보인다는 browser truth를 직접 잠급니다.
- scenario count 16 유지 주장도 맞습니다. `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `16`이었습니다.
- 이번 라운드의 production 코드, service regression, docs 추가 변경은 없습니다. `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`는 이미 history-card badge downgrade shipped truth를 설명하고 있었고, scenario count도 늘지 않았기 때문에 docs sync가 새로 필요하지 않았습니다.
- 범위도 현재 projectH 방향에서 벗어나지 않습니다. 이 라운드는 strong/weak/unresolved slot clarity 축 안에서 zero-strong-slot entity-card badge semantics를 browser history-card header까지 맞추는 same-family user-visible hardening 1건입니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `make e2e-test`
  - 통과 (`16 passed`)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-zero-strong-slot-history-card-badge-playwright-smoke.md`
  - `verify/3/31/2026-03-31-zero-strong-slot-natural-reload-exact-field-verification.md`
  - `.pipeline/codex_feedback.md`
  - `e2e/tests/web-smoke.spec.mjs`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `python3 -m unittest -v tests.test_web_app`
  - 이유: 이번 변경은 `e2e/tests/web-smoke.spec.mjs`의 browser smoke assertion 1건만 확장한 e2e-only slice였고, service/production hunk가 없어서 unit/service suite를 다시 돌릴 필요는 없었습니다.

## 남은 리스크
- zero-strong-slot entity-card badge semantics family는 현재 shipped surface 기준으로 truthfully 닫힌 것으로 봅니다. initial response downgrade, history summary serialization, history-card reload exact field, natural reload exact field, browser history-card badge render까지 explicit coverage가 있습니다.
- 이 상태에서 broad axis `Distinguish strong facts, single-source facts, and unresolved slots more clearly` 안의 다음 slice는 자동으로 하나를 고르기 어렵습니다. local docs/tests 기준으로는 최소 두 후보가 남습니다:
  - weak-slot reinvestigation / source-consensus regression fixture improvement
  - single-source fact vs unresolved slot user-visible classification clarity
- 따라서 이번 handoff는 `STATUS: needs_operator`로 두고, operator가 위 broad axis 안에서 exact next slice 1개를 다시 확정하는 편이 정직합니다.
