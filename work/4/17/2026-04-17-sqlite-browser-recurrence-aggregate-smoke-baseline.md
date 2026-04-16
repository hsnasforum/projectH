# sqlite-browser-recurrence-aggregate-smoke-baseline

## 변경 파일

- `e2e/playwright.sqlite.config.mjs` (신규)
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 shared aggregate builder seam이 수정되어 service-level sqlite parity가 27건+ 모두 green으로 마감됨. 남은 same-family current-risk는 user-visible layer: `storage_backend='sqlite'`가 shipped opt-in seam이지만 현재 Playwright smoke는 JSON defaults에서만 구동됨. 기존 browser smoke 경로를 sqlite 환경에서도 검증하여 browser-visible contract의 sqlite parity gate를 확보.

## 핵심 변경

1. **`e2e/playwright.sqlite.config.mjs`** (신규): `app.web`을 port 8880에서 `LOCAL_AI_STORAGE_BACKEND=sqlite` + isolated temp dirs(`sqlite DB, notes, corrections, web-search`)로 구동하는 dedicated Playwright config. 기존 `web-smoke.spec.mjs` 시나리오를 `-g` filter로 선택 실행.

2. **browser smoke 통과 확인**:
   - `same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다` — sqlite 백엔드에서 aggregate 형성 → emit → apply → confirm 전체 lifecycle이 browser에서 정상 동작
   - `same-session recurrence aggregate stale candidate retires before apply start` — sqlite 백엔드에서 supporting correction supersede 시 aggregate가 stale로 퇴출되는 browser 계약이 정상 동작

3. **docs sync**: `README.md`에 SQLite Browser Smoke 섹션 추가, `docs/ACCEPTANCE_CRITERIA.md`에 sqlite browser gate 시나리오 2건 추가, `docs/MILESTONES.md`에 sqlite browser baseline milestone 추가, `docs/TASK_BACKLOG.md`에 sqlite 항목 browser parity gate 반영.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다" --reporter=line  # 1 passed
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate stale candidate retires before apply start" --reporter=line  # 1 passed
git diff --check -- e2e/playwright.sqlite.config.mjs e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

## 남은 리스크

- 현재 sqlite browser gate는 recurrence aggregate lifecycle 2건에 한정. 다른 JSON-default smoke 시나리오의 sqlite parity 확대는 이번 슬라이스 scope 밖.
- `e2e/playwright.sqlite.config.mjs`는 `os.tmpdir()`에 temp dir를 생성하므로 CI에서 cleanup이 필요할 수 있음 (현재 local dev 환경에서는 OS가 관리).
- `web-smoke.spec.mjs` 테스트 코드 자체는 변경 없음 — 기존 시나리오를 sqlite config로 재실행하는 additive 구조.
