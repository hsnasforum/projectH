# sqlite-browser-document-summary-search-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- `using-superpowers`

## 변경 이유

이전 `/work`에서 sqlite browser gate가 recurrence aggregate 5건 + document-loop save/correction/verdict 4건까지 확장됐고, 최신 `/verify`는 같은 opt-in sqlite browser 축에서 다음 current-risk가 core document productivity loop (요약 본문/근거/요약 구간, 브라우저 파일 선택 요약, 폴더 선택 검색, 검색-only hidden-body + preview card) 네 건이라고 판단했습니다. 이 네 시나리오는 JSON-default Playwright path에서 이미 shipped된 사용자 가시 계약이고, sqlite backend에서도 동일하게 동작한다는 증거가 그동안 없었습니다. 이번 라운드는 기존 `web-smoke.spec.mjs` 네 시나리오를 `playwright.sqlite.config.mjs`로 재실행해서 실측 parity gate를 확보하고, sqlite browser gate inventory 문서를 13건 기준으로 맞춥니다. 제품 계약은 손대지 않습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인** (기존 시나리오 재사용, 코드·설정 변경 없음):
   - `파일 요약 후 근거와 요약 구간이 보입니다` — sqlite backend에서도 요약 응답 본문 + 근거 패널 + 요약 구간 + quick-meta/transcript-meta source label이 정상 노출됨을 직접 확인.
   - `브라우저 파일 선택으로도 파일 요약이 됩니다` — browser file picker 기반 요약 플로우가 sqlite backend에서도 기존 contract 그대로 동작함을 확인.
   - `브라우저 폴더 선택으로도 문서 검색이 됩니다` — folder picker 기반 검색 요약(`선택 결과 요약`, preview cards, count-based metadata)이 sqlite backend에서도 동일하게 렌더됨을 확인.
   - `검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다` — search-only 응답의 hidden-body + preview card + selected-path copy 거동이 sqlite backend에서도 유지됨을 확인.

2. **docs sync**: sqlite browser gate inventory 문서 4개에 core document productivity loop 4건을 추가해 전체 13건으로 맞춤.
   - `README.md` `SQLite Browser Smoke (opt-in backend parity gate)` 섹션의 시나리오 목록을 13건으로 확장.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite browser smoke bullet에 core loop 4건 추가.
   - `docs/MILESTONES.md` SQLite browser smoke baseline milestone 문구에 core document productivity loop 4건 포함으로 확장.
   - `docs/TASK_BACKLOG.md` `Partial / Opt-In` SQLite backend 항목의 browser-level parity gate 설명을 같은 13건으로 확장.

3. **제품/서비스/설정 무변경**: `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`, app/serializer/store/frontend 모두 손대지 않음. sqlite 전용 요약/검색 플로우 없음.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "파일 요약 후 근거와 요약 구간이 보입니다" --reporter=line  # 1 passed (7.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "브라우저 파일 선택으로도 파일 요약이 됩니다" --reporter=line  # 1 passed (5.4s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "브라우저 폴더 선택으로도 문서 검색이 됩니다" --reporter=line  # 1 passed (4.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다" --reporter=line  # 1 passed (4.3s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다" --reporter=line  # 1 passed (8.4s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate stale candidate retires before apply start" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate active lifecycle survives supporting correction supersession" --reporter=line  # 1 passed (5.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate recorded basis label survives supporting correction supersession" --reporter=line  # 1 passed (5.4s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다" --reporter=line  # 1 passed (8.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다" --reporter=line  # 1 passed (5.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다" --reporter=line  # 1 passed (6.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다" --reporter=line  # 1 passed (6.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다" --reporter=line  # 1 passed (5.8s)
git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 opt-in sqlite browser gate inventory 4건을 실측으로 확정하고 기존 9건 회귀가 없음을 확인한 Playwright-only smoke tightening bundle이었으며, 최신 handoff가 요구한 focused rerun 4건 + 기존 9건 전부 green을 확인했기 때문에 full browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- sqlite browser gate는 이번 라운드로 recurrence aggregate 5건 + document-loop save/correction/verdict 4건 + core document productivity loop 4건까지 총 13건으로 확장됐습니다. OCR/PDF 혼합 읽기, 권한 게이트, history-card reload, 웹 조사 계열은 이번 슬라이스 scope 밖이라 아직 sqlite backend로 확인되지 않았습니다.
- `LOCAL_AI_NOTES_DIR`을 repo 기본값으로 공유하는 sqlite config 정책은 지난 라운드 그대로이며, sqlite/JSON smoke config를 병렬 실행하는 파이프라인이 생기면 격리 전략을 다시 봐야 합니다.
- `stop-reverse-conflict` 시나리오는 이전 라운드부터 관찰된 "세션 리부팅 직후 1회 산발 timeout" 경향이 유지됩니다. 이번 라운드에서도 첫 실행이 아닌 isolated 재실행은 안정적으로 통과했고, Python service-level 재구성으로는 문제가 재현되지 않아 CI에서 반복 재현되지 않는 한 sqlite-specific 회귀로 보기 어렵습니다. CI 환경에서 재현되면 Playwright webServer 정리 타이밍을 같이 봐야 합니다.
