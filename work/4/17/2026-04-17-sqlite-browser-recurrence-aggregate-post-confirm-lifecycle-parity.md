# sqlite-browser-recurrence-aggregate-post-confirm-lifecycle-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- `using-superpowers`

## 변경 이유

이전 `/work`에서 sqlite browser gate baseline 두 건(emitted-apply-confirm lifecycle, stale candidate retirement)을 `e2e/playwright.sqlite.config.mjs`로 닫았습니다. 최신 `/verify`는 같은 family의 남은 current-risk가 post-confirm user-visible lifecycle — active lifecycle survives supersession, recorded-basis label survives supersession, stop-reverse-conflict cleanup — 이라고 판단했고, 세 시나리오는 동일한 post-confirm setup과 검증 축을 공유하므로 micro-slice로 쪼개기보다 하나의 bounded bundle로 닫는 편이 맞다고 정리했습니다. 이번 라운드는 코드 변경 없이 기존 `web-smoke.spec.mjs` 세 시나리오가 sqlite backend에서도 실제로 통과함을 확인하고, sqlite browser gate inventory 문서를 사용자/운영자가 의존할 수 있는 목록으로 맞췄습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인**: 기존 Playwright 시나리오 세 건을 `playwright.sqlite.config.mjs`로 재실행해서 opt-in sqlite backend에서도 동일한 browser 계약이 유지됨을 확인.
   - `same-session recurrence aggregate active lifecycle survives supporting correction supersession` — active effect가 supporting correction supersession 이후에도 계속 활성화된 상태로 보이는지 sqlite 경로로 직접 확인.
   - `same-session recurrence aggregate recorded basis label survives supporting correction supersession` — `[기록된 기준]` label이 supersession 이후에도 끊기지 않고 유지되는지 sqlite 경로로 직접 확인.
   - `same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다` — stop/reverse/conflict-visibility 단계가 sqlite에서 기록·재렌더링까지 정상 동작하는지 직접 확인.

2. **docs sync**: sqlite browser gate inventory에 위 세 시나리오를 추가.
   - `README.md` `SQLite Browser Smoke (opt-in backend parity gate)` 섹션의 시나리오 목록을 5건으로 확장.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite browser smoke bullet에 post-confirm active lifecycle / recorded basis label / stop-reverse-conflict cleanup 3건 추가.
   - `docs/MILESTONES.md` SQLite browser smoke baseline milestone 문구를 post-confirm lifecycle 3건 포함으로 확장.
   - `docs/TASK_BACKLOG.md` `Partial / Opt-In` SQLite backend 항목의 browser-level parity gate 설명을 같은 5건으로 확장.

3. **제품/서비스 코드 무변경**: `e2e/playwright.sqlite.config.mjs`와 `e2e/tests/web-smoke.spec.mjs` 본문은 그대로 재사용. sqlite-only 플로우를 도입하지 않고 JSON-default에서 이미 shipped된 browser 계약을 sqlite backend에서 재확인하는 additive 구조 유지.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate active lifecycle survives supporting correction supersession" --reporter=line  # 1 passed (5.4s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate recorded basis label survives supporting correction supersession" --reporter=line  # 1 passed (5.3s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다" --reporter=line  # 1 passed (9.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다" --reporter=line  # 1 passed (8.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate stale candidate retires before apply start" --reporter=line  # 1 passed (4.6s)
git diff --check -- e2e/playwright.sqlite.config.mjs e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 opt-in sqlite browser gate inventory 3건을 실측으로 확정하고 sqlite browser gate 문서를 5건 기준으로 맞추는 Playwright-only smoke tightening bundle이었고, 최신 handoff가 요구한 focused rerun 3건과 baseline 2건을 모두 확인했기 때문에 full browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- 첫 실행에서 `stop-reverse-conflict` 시나리오가 일시적으로 `aggregate-trigger-conflict-checked` label을 기다리다 timeout으로 실패하는 산발 관찰이 있었습니다. 동일 config로 3회 연속 재실행한 결과 모두 `1 passed`로 안정화되었고, 동일 플로우를 Python service-level (`check_aggregate_conflict_visibility` via `SQLiteSessionStore`)로 직접 재구성해도 CV record가 정상적으로 방출/직렬화되는 것을 확인했으므로, CI에서 반복되는 회귀가 아니라 이전 Playwright webServer 정리가 덜 된 상태에서 발생한 일회성 flake로 판단합니다. CI 환경에서 재현되면 `e2e/playwright.sqlite.config.mjs`의 `fs.mkdtempSync` 경로 정리·`reuseExistingServer` 관련 설정을 같이 봐야 합니다.
- sqlite browser gate는 이번 라운드로 recurrence aggregate의 pre-confirm 2건 + post-confirm 3건까지 확장되었고, 그 밖의 JSON-default browser smoke 시나리오(summary source-label, 권한 게이트, history-card reload 등)를 sqlite backend에서 같이 돌려보는 일은 이번 슬라이스 scope 밖입니다.
- `e2e/playwright.sqlite.config.mjs`는 여전히 `os.tmpdir()`에 temp dir를 생성하며, local dev 환경에서는 OS가 관리하지만 CI에서는 별도 cleanup이 필요할 수 있습니다.
