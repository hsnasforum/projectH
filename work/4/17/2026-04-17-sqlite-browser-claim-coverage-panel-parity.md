# sqlite-browser-claim-coverage-panel-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

이전 `/work`에서 sqlite browser gate가 총 24건(recurrence aggregate 5 + document-loop save/correction/verdict 4 + core document productivity loop 4 + PDF/OCR document workflow 4 + reviewed-memory candidate/review-queue surface 3 + core approval save path 2 + core chat shell 2)까지 확장됐습니다. 최신 `/verify`는 history-card reload / 웹 조사 체인으로 넘어가기 전에 닫을 남은 same-family current-risk가 shipped claim-coverage panel 네 건(`status tag + 행동 힌트`, `재조사 대상 슬롯 진행 상태`, `재조사 후 보강 슬롯`, `재조사 후 약화 슬롯`)이라고 판단했습니다. 이 네 시나리오는 JSON-default Playwright path에서 이미 shipped된 사용자 가시 계약이고, sqlite backend에서도 동일하게 동작한다는 증거가 그동안 없었습니다. 이번 라운드는 기존 `web-smoke.spec.mjs` 네 시나리오를 `playwright.sqlite.config.mjs`로 재실행해서 실측 parity gate를 확보하고 sqlite browser gate inventory 문서를 28건 기준으로 맞춥니다. claim-coverage 렌더링 semantics와 저장 계약은 손대지 않습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인** (기존 시나리오 재사용, 코드·설정 변경 없음):
   - `claim-coverage panel은 status tag와 행동 힌트를 올바르게 렌더링합니다` — sqlite backend에서도 leading status tag와 행동 힌트가 동일하게 노출됨을 확인.
   - `claim-coverage panel은 재조사 대상 슬롯의 진행 상태를 명확히 렌더링합니다` — sqlite backend에서도 reinvestigation-target slot의 진행 상태가 동일하게 렌더됨을 확인.
   - `claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다` — sqlite backend에서도 `reinforced` 슬롯 표시가 기존 plain-language 문구 그대로 유지됨을 확인.
   - `claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다` — sqlite backend에서도 `regressed` 슬롯 표시가 기존 plain-language 문구 그대로 유지됨을 확인.

2. **docs sync**: sqlite browser gate inventory 문서 4개에 claim-coverage panel 4건을 추가해 총 28건으로 맞춤.
   - `README.md` `SQLite Browser Smoke (opt-in backend parity gate)` 섹션의 시나리오 목록을 28건으로 확장.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite browser smoke bullet에 claim-coverage panel 4건 추가.
   - `docs/MILESTONES.md` SQLite browser smoke baseline milestone 문구에 claim-coverage panel 4건 포함으로 확장.
   - `docs/TASK_BACKLOG.md` `Partial / Opt-In` SQLite backend 항목의 browser-level parity gate 설명을 같은 28건으로 확장.

3. **제품/서비스/설정 무변경**: `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`, app/serializer/store/frontend 모두 손대지 않음. sqlite 전용 claim-coverage 플로우 없음.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "claim-coverage panel은 status tag와 행동 힌트를 올바르게 렌더링합니다" --reporter=line  # 1 passed (4.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "claim-coverage panel은 재조사 대상 슬롯의 진행 상태를 명확히 렌더링합니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다" --reporter=line  # 1 passed (3.4s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다" --reporter=line  # 1 passed (4.0s)
git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 opt-in sqlite browser gate inventory 4건을 실측으로 확정한 Playwright-only smoke tightening bundle이었고, 최신 handoff가 요구한 focused rerun 4건을 모두 확인했습니다. 기존 24건 sqlite browser gate는 이전 라운드에서 회귀 없음이 확인됐고 이번 슬라이스는 설정·코드·테스트 본문 어디에도 변경을 만들지 않았으므로 full sqlite browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- sqlite browser gate는 이번 라운드로 총 28건까지 확장됐습니다. history-card reload, web-search history header badges, natural-language reload 체인, provenance exact-field 계열은 이번 슬라이스 scope 밖이라 아직 sqlite backend로 확인되지 않았습니다.
- claim-coverage는 여전히 shipped secondary-mode surface이며, 이번 라운드에서 focus-slot plain-language 계약(`reinforced` / `regressed` / still single-source / still unresolved)은 저장 semantics가 아니라 UI 문구로만 검증됐습니다.
- `LOCAL_AI_NOTES_DIR`을 repo 기본값으로 공유하는 sqlite config 정책은 지난 라운드 그대로이며, sqlite/JSON smoke config를 병렬 실행하는 파이프라인이 생기면 격리 전략을 다시 봐야 합니다.
- `stop-reverse-conflict` 시나리오의 "세션 리부팅 직후 1회 산발 timeout" 경향은 이번 라운드에서도 영향이 없었습니다. CI에서 재현되면 이전 라운드 기록대로 Playwright webServer 정리 타이밍을 함께 점검해야 합니다.
