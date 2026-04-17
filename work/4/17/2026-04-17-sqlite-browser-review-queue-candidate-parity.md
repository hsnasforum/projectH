# sqlite-browser-review-queue-candidate-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- `using-superpowers`

## 변경 이유

이전 `/work`에서 sqlite browser gate가 recurrence aggregate 5 + save/correction/verdict 4 + core document productivity loop 4 + PDF/OCR document workflow 4건까지 총 17건으로 확장됐습니다. 최신 `/verify`는 같은 reviewed-memory family의 다음 current-risk가 shipped candidate/review-queue 서피스 세 건(`candidate confirmation path는 save support와 분리`, `review-queue reject/defer는 accept와 동일한 quick-meta/transcript-meta/stale-clear`, `review-queue reject-defer aggregate support visibility`)이라고 판단했습니다. 이 세 시나리오는 JSON-default Playwright path에서 이미 shipped된 사용자 가시 계약이고, sqlite backend에서도 동일하게 동작한다는 증거가 그동안 없었습니다. 이번 라운드는 기존 `web-smoke.spec.mjs` 세 시나리오를 `playwright.sqlite.config.mjs`로 재실행해서 실측 parity gate를 확보하고 sqlite browser gate inventory 문서를 20건 기준으로 맞춥니다. 제품 계약·approval semantics·reviewed-memory 경계는 손대지 않습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인** (기존 시나리오 재사용, 코드·설정 변경 없음):
   - `candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다` — sqlite backend에서도 candidate confirmation 기록이 save support/`session_local_candidate`와 분리되고 later correction으로 current state에서 사라지는 계약이 유지됨을 확인.
   - `review-queue reject/defer는 accept와 동일한 quick-meta, transcript-meta, stale-clear 경로를 따릅니다` — sqlite backend에서도 review-queue reject/defer가 accept와 같은 quick-meta, transcript-meta, follow-up retention, stale-clear 경로를 따름을 확인. payload에 `review_action`/`review_status`도 기존과 동일하게 기록됨.
   - `review-queue reject-defer aggregate support visibility` — sqlite backend에서도 reject/defer 처리 이후 aggregate support visibility가 truthful하게 유지됨을 확인.

2. **docs sync**: sqlite browser gate inventory 문서 4개에 reviewed-memory candidate/review-queue 서피스 3건을 추가해 총 20건으로 맞춤.
   - `README.md` `SQLite Browser Smoke (opt-in backend parity gate)` 섹션의 시나리오 목록을 20건으로 확장.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite browser smoke bullet에 candidate/review-queue 3건 추가.
   - `docs/MILESTONES.md` SQLite browser smoke baseline milestone 문구에 reviewed-memory candidate/review-queue surface 3건 포함으로 확장.
   - `docs/TASK_BACKLOG.md` `Partial / Opt-In` SQLite backend 항목의 browser-level parity gate 설명을 같은 20건으로 확장.

3. **제품/서비스/설정 무변경**: `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`, app/serializer/store/frontend 모두 손대지 않음. sqlite 전용 candidate/review-queue 플로우 없음.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다" --reporter=line  # 1 passed (9.5s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "review-queue reject/defer는 accept와 동일한 quick-meta, transcript-meta, stale-clear 경로를 따릅니다" --reporter=line  # 1 passed (10.6s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "review-queue reject-defer aggregate support visibility" --reporter=line  # 1 passed (4.9s)
git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 opt-in sqlite browser gate inventory 3건을 실측으로 확정한 Playwright-only smoke tightening bundle이었고, 최신 handoff가 요구한 focused rerun 3건을 모두 확인했습니다. 기존 17건 sqlite browser gate는 이전 라운드에서 회귀 없음이 확인됐고 이번 슬라이스는 설정·코드·테스트 본문 어디에도 변경을 만들지 않았으므로 full sqlite browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- sqlite browser gate는 이번 라운드로 총 20건(recurrence aggregate 5 + document-loop save/correction/verdict 4 + core document productivity loop 4 + PDF/OCR document workflow 4 + reviewed-memory candidate/review-queue surface 3)까지 확장됐습니다. 권한 게이트, history-card reload, 웹 조사 계열은 이번 슬라이스 scope 밖이라 아직 sqlite backend로 확인되지 않았습니다.
- reviewed-memory 경계는 이번 라운드에서도 shipped 계약 그대로이며, review-queue `accept` / `reject` / `defer`는 여전히 reviewed-but-not-applied 액션으로만 동작합니다. user-level memory로의 확장은 여전히 제품 scope 밖입니다.
- `LOCAL_AI_NOTES_DIR`을 repo 기본값으로 공유하는 sqlite config 정책은 지난 라운드 그대로이며, sqlite/JSON smoke config를 병렬 실행하는 파이프라인이 생기면 격리 전략을 다시 봐야 합니다.
- `stop-reverse-conflict` 시나리오의 "세션 리부팅 직후 1회 산발 timeout" 경향은 이번 라운드에서는 영향이 없었습니다. CI에서 재현되면 이전 라운드 기록대로 Playwright webServer 정리 타이밍을 함께 점검해야 합니다.
