STATUS: verified
CONTROL_SEQ: 259
BASED_ON_WORK: work/4/26/2026-04-26-e2e-healthcheck-wrapper-audit.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 258
VERIFIED_BY: Claude
NEXT_CONTROL: advisory_request.md CONTROL_SEQ 259

---

# 2026-04-26 E2E healthcheck wrapper audit 검증

## 이번 라운드 범위

정적 코드 감사 결과 검증. 변경된 tracked 파일 없음 — work note 자체가 유일한 산출물.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `git diff --check --` | **PASS** (변경된 tracked 파일 없음) |
| `git status -- Makefile e2e/start-server.sh e2e/playwright.config.mjs` | **PASS** (읽기 전용 대상 변경 없음) |

## 정적 감사 주장 spot-check

**`e2e/start-server.sh` 핵심 라인 직접 확인:**

| work note 주장 | 실제 코드 | 일치 |
|----------------|-----------|------|
| `8-11`: HOST/PORT/HEALTH_URL/WAIT_SECONDS 기본값 | `HOST="${E2E_HOST:-127.0.0.1}"`, `PORT="${E2E_PORT:-8879}"`, `HEALTH_URL="…/healthz"`, `WAIT_SECONDS="${…:-60}"` | ✓ |
| `16-26`: `healthcheck()` — Python urllib HTTP 200 체크 | lines 16–27 정확히 일치 | ✓ |
| `29-37`: `cleanup()` — SERVER_PID kill + TMP_DIR rm | lines 29–37 정확히 일치 | ✓ |
| `50-53`: existing-server 분기 — healthcheck 성공 시 바로 `run_tests` 후 exit | `if healthcheck; then … run_tests "$@"; exit $?; fi` (SERVER_PID 미설정, trap 미등록) | ✓ |
| `56-71`: no-server 분기 — TMP_DIR + trap + mock env + `python3 -m app.web` 백그라운드 | lines 56–71 정확히 일치 | ✓ |
| `57-59`: EXIT/INT/TERM trap 등록 | `trap 'status=$?; cleanup; exit "$status"' EXIT`, `trap 'exit 130' INT`, `trap 'exit 143' TERM` | ✓ |
| `73-91`: 1초 간격 healthcheck loop, 조기 종료 감지, timeout | lines 73–91 정확히 일치 | ✓ |

**`Makefile:12-13`:**
- `e2e-test:` → `e2e/start-server.sh` 직접 호출, 별도 환경 변수 없음 ✓

**`e2e/playwright.config.mjs`:**
- `baseURL: "http://127.0.0.1:8879"` (line ~20) ✓
- `reuseExistingServer: true`, `url: "http://127.0.0.1:8879"` webServer 설정 ✓
- `timeout: 60_000` (wrapper의 WAIT_SECONDS 60s와 일치) ✓

## Release Gate Truth 요약 (정적 감사 기준)

**No-server 경로:**
- wrapper가 port 8879에 mock `app.web`을 시작, `/healthz` HTTP 200까지 최대 60s 대기
- 시작 실패 또는 timeout 시 비정상 종료
- EXIT trap으로 SERVER_PID kill + TMP_DIR cleanup 보장

**Existing-server 경로:**
- wrapper 시작 직후 healthcheck 성공 시 기존 서버 재사용, `run_tests` 후 exit
- `SERVER_PID` / cleanup trap 설정 전 분기이므로 기존 서버 kill 없음 보장
- 재사용 판단 기준: 포트 점유가 아닌 `/healthz` HTTP 200 응답

## 미검증 (정직한 보고)

- live Playwright 실행: sandbox 제약으로 미실행 (handoff 범위 제한)
- `/healthz`는 200이지만 Playwright baseURL 경로가 비정상인 edge case: 정적 감사 범위 밖
- sqlite smoke config(`playwright.sqlite.config.mjs`): 기본 `make e2e-test` 경로와 별도

## 현재 Dirty Tree 상태

| 파일 | 커밋 여부 |
|------|-----------|
| `work/4/26/2026-04-26-e2e-healthcheck-wrapper-audit.md` | 미커밋 (untracked) |
| `verify/4/26/2026-04-26-e2e-healthcheck-wrapper-audit.md` | 미커밋 (이 파일) |

`docs/ARCHITECTURE.md`, `docs/MILESTONES.md` 등 이전 라운드 산출물은 `aed6bb3`으로 커밋 완료.

## 남은 과제

- work note + verify note 커밋 (verify-lane)
- M43 milestone 방향 — advisory에서 확정 필요 ("Next 3" 항목 2)
- MILESTONES.md "Next 3" 항목 1(E2E 환경 개선 검증): 정적 감사 완료 사실 반영 여부 — advisory에서 결정
