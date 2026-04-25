STATUS: verified
CONTROL_SEQ: 150
BASED_ON_WORK: work/4/25/2026-04-25-m31-release-gate-retry-e2e-start-failure.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 150 (e2e webServer spawn fix: reuseExistingServer + Makefile pre-start)

---

## M31 Axis 1 retry: release gate E2E 기동 실패 (2차)

### Verdict

RECORDED + ROOT CAUSE IDENTIFIED (코드 회귀 아님). E2E gate가 동일한 PermissionError로 재실패. 추가 진단으로 근본 원인 확인: `e2e/playwright.config.mjs:36`의 `reuseExistingServer: false`가 Playwright가 webServer를 Node.js 자식 프로세스로 항상 스폰하게 만들고, 이 WSL2 환경에서 해당 경로가 socket PermissionError를 냄.

### Root Cause Confirmed

```
e2e/playwright.config.mjs:36  reuseExistingServer: false
```

Playwright가 `webServer.command`(`bash -lc 'python3 -m app.web ...'`)를 Node.js 자식 프로세스로 스폰 → WSL2에서 해당 자식 프로세스가 `socket.socket(AF_INET, SOCK_STREAM)` 실패 (`PermissionError: [Errno 1]`).

**검증 대조 실험:**
- `python3 -m app.web --host 127.0.0.1 --port 8879` 직접 기동 → HTTP 302 정상
- 프리-기동 서버 상태에서 `npx playwright test ... -g "파일 요약..."` → 1 passed (9.7s)
- Playwright가 서버를 자식 프로세스로 스폰하는 `make e2e-test` → PermissionError

### Checks Run (verify 추가 진단)

- `grep -n "reuseExisting" e2e/playwright.config.mjs` → `reuseExistingServer: false` (line 36) 확인
- `e2e/playwright.config.mjs` 전체 webServer 섹션 확인: `bash -lc '...'` 명령, `url: http://127.0.0.1:8879`, timeout 60s
- `e2e/package.json` 확인: `"test": "playwright test"` (단순 Playwright 호출)
- `Makefile` e2e-test 확인: `cd e2e && npm test` (서버 사전 기동 없음)
- 216 unit tests (watcher_core + watcher_signals + controller_monitor) → `Ran 216 tests OK`
- `python3 -m py_compile watcher_core.py watcher_signals.py controller/monitor.py` → OK

### What Was Not Checked

- `make e2e-test` 전체: 근본 원인이 확인되어 재실행 보류 — 다음 implement에서 fix 후 실행.

### Fix: Bounded 2-File Change

```
e2e/playwright.config.mjs  — reuseExistingServer: false → true
Makefile                   — e2e-test 타겟: 서버 사전 기동 추가
```

서버를 Node.js 프로세스 트리 밖에서 기동한 뒤 Playwright가 기존 서버를 재사용하도록 전환. M30 구조 변경으로 인한 코드 회귀는 없음 (216 unit tests PASS).
