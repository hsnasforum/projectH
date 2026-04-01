# 2026-03-31 history-card reload smoke docs sync verification

## 변경 파일
- `verify/3/31/2026-03-31-history-card-reload-smoke-docs-sync-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest Claude `/work`인 `work/3/31/2026-03-31-history-card-reload-smoke-docs-sync.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-history-card-reload-badge-playwright-smoke-verification.md`를 기준으로 이번 라운드 문서 동기화 주장만 다시 대조할 필요가 있었습니다.
- 직전 `/verify`에서 history-card reload Playwright smoke 추가 자체는 truthful하지만 docs sync가 빠졌다고 남겼으므로, 이번 라운드는 그 docs sync가 실제로 맞는지와 범위가 과장되지 않았는지를 확인해야 했습니다.

## 핵심 변경
- latest `/work`의 docs-only 범위 주장은 사실이며, 현재 변경은 local-first document assistant MVP의 browser smoke 문서 정합성 보강 범위 안에 머물러 있습니다.
- 다만 latest `/work` closeout의 변경 요약은 실제 수정 폭을 축소해 적었습니다. 실제 diff는 scenario 16 추가만이 아니라 source-type label / transcript meta / claim-coverage / web-search history badge smoke 관련 기존 계약 설명까지 함께 동기화합니다.
- 현재 문서 상태는 기존 Playwright smoke 계약과 정합적입니다. `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md` 모두 16-scenario 기준과 history-card reload 유지 항목을 반영하고 있습니다.
- 전체 프로젝트 방향 이탈이나 별도 trajectory audit이 필요한 징후는 이번 라운드에서 보이지 않아 `report/`는 만들지 않았습니다.

## 검증
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md` : 통과
- `rg -n "15 browser scenarios|16 browser scenarios|history-card 다시 불러오기|설명 카드|reload badge|백과 기반|설명형 단일 출처" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md` : 관련 문구 반영 확인
- `rg -n "history-card|header badge|claim-coverage|negative source-type|source-type|출처 2개|문서 요약|선택 결과 요약|설명 카드|설명형 단일 출처|백과 기반" e2e/tests/web-smoke.spec.mjs` : 문서가 가리키는 smoke assertion 근거 확인
- `rg -n "^test\\(" e2e/tests/web-smoke.spec.mjs` : Playwright smoke 시나리오 16개 확인
- 이번 라운드에서는 product code나 test file이 바뀌지 않았으므로 `make e2e-test`와 `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. underlying smoke/test 재실행 truth는 `verify/3/31/2026-03-31-history-card-reload-badge-playwright-smoke-verification.md`에 남아 있습니다.

## 남은 리스크
- canonical product/docs truth는 현재 파일과 이 `/verify` 메모 기준으로는 맞지만, latest `/work` closeout은 실제 문서 수정 범위를 덜 적었습니다.
- dirty worktree가 넓어 다음 검증도 계속 범위를 좁혀 보아야 합니다.
