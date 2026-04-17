# sqlite-browser-web-search-history-card-header-badges-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

이전 `/work`에서 sqlite browser gate가 총 28건까지 확장됐습니다. 최신 `/verify`는 history-card reload / 자연어 reload 체인으로 넘어가기 전에 닫을 남은 same-family current-risk가 shipped web-search history-card header/meta composition 계약(`answer-mode`, `verification-strength`, `source-role trust` badges + `.meta` count/progress composition 순서)이라고 판단했습니다. 이 시나리오는 JSON-default Playwright path에서 이미 shipped된 사용자 가시 계약이고, sqlite backend에서도 동일하게 동작한다는 증거가 그동안 없었습니다. 이번 라운드는 기존 `web-smoke.spec.mjs` 한 시나리오를 `playwright.sqlite.config.mjs`로 재실행해서 실측 parity gate를 확보하고 sqlite browser gate inventory 문서를 29건 기준으로 맞춥니다. history-card 렌더링 semantics와 저장 record shape는 손대지 않습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인** (기존 시나리오 재사용, 코드·설정 변경 없음):
   - `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다` — sqlite backend에서도 answer-mode badge(investigation vs general), verification-strength badge text/class, source-role trust badge text/class, 그리고 `.meta`의 count/progress composition 순서가 JSON-default와 동일하게 유지되며 separator 아티팩트나 label leak이 없음을 확인.

2. **docs sync**: sqlite browser gate inventory 문서 4개에 history-card header badges 1건을 추가해 총 29건으로 맞춤.
   - `README.md` `SQLite Browser Smoke (opt-in backend parity gate)` 섹션의 시나리오 목록을 29건으로 확장.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite browser smoke bullet에 history-card header badges 1건 추가.
   - `docs/MILESTONES.md` SQLite browser smoke baseline milestone 문구에 history-card header badges 1건 포함으로 확장.
   - `docs/TASK_BACKLOG.md` `Partial / Opt-In` SQLite backend 항목의 browser-level parity gate 설명을 같은 29건으로 확장.

3. **제품/서비스/설정 무변경**: `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`, app/serializer/store/frontend 모두 손대지 않음. sqlite 전용 history-card 렌더링/record shape 변경 없음.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line  # 1 passed (4.1s)
git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 opt-in sqlite browser gate inventory 1건을 실측으로 확정한 Playwright-only smoke tightening bundle이었고, 최신 handoff가 요구한 focused rerun 1건을 확인했습니다. 기존 28건 sqlite browser gate는 이전 라운드에서 회귀 없음이 확인됐고 이번 슬라이스는 설정·코드·테스트 본문 어디에도 변경을 만들지 않았으므로 full sqlite browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- sqlite browser gate는 이번 라운드로 총 29건까지 확장됐습니다. history-card reload, 자연어 reload 체인, provenance exact-field 계열은 이번 슬라이스 scope 밖이라 아직 sqlite backend로 확인되지 않았습니다.
- history-card header badges는 여전히 shipped secondary-mode UI 계약이며, 이번 라운드에서 answer-mode 구분, verification-strength, source-role trust, `.meta` composition은 UI 렌더링 수준에서만 검증됐습니다.
- `LOCAL_AI_NOTES_DIR`을 repo 기본값으로 공유하는 sqlite config 정책은 지난 라운드 그대로이며, sqlite/JSON smoke config를 병렬 실행하는 파이프라인이 생기면 격리 전략을 다시 봐야 합니다.
- `stop-reverse-conflict` 시나리오의 "세션 리부팅 직후 1회 산발 timeout" 경향은 이번 라운드에서도 영향이 없었습니다. CI에서 재현되면 이전 라운드 기록대로 Playwright webServer 정리 타이밍을 함께 점검해야 합니다.
