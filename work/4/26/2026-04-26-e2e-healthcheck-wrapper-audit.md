# 2026-04-26 E2E healthcheck wrapper audit

## 변경 파일
- `work/4/26/2026-04-26-e2e-healthcheck-wrapper-audit.md`

## 사용 skill
- `work-log-closeout`: 정적 감사 근거, 실제 실행 체크, 미실행 체크, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- `make e2e-test`가 사용하는 `e2e/start-server.sh` healthcheck wrapper의 no-server / existing-server 동작을 live Playwright 실행 없이 정적 코드 근거로 확인해야 했다.
- M42 closure release gate truth로 사용할 수 있도록 서버 재사용 조건, mock `app.web` 시작 방식, ready 판단, cleanup 보장을 `/work` 기록에 남겼다.

## 핵심 변경
- 코드, 테스트, 제품 문서는 수정하지 않았다. `Makefile`, `e2e/start-server.sh`, `e2e/playwright.*.mjs`는 읽기 전용으로만 확인했다.
- Makefile 근거: `Makefile:12-13`에서 `e2e-test` 타겟은 별도 환경 변수 없이 `e2e/start-server.sh`를 직접 호출한다. 따라서 기본 host/port/mock 동작은 wrapper 스크립트가 결정한다.
- No-server 경로 근거: `e2e/start-server.sh:8-11`은 기본 `HOST=127.0.0.1`, `PORT=8879`, `HEALTH_URL=http://${HOST}:${PORT}/healthz`, `WAIT_SECONDS=60`을 사용한다. `e2e/start-server.sh:56-71`은 임시 DB 디렉터리를 만들고 `LOCAL_AI_MODEL_PROVIDER=mock`, `LOCAL_AI_MOCK_STREAM_DELAY_MS=10`, `LOCAL_AI_SQLITE_DB_PATH=$TMP_DIR/test.db`로 `python3 -m app.web --host "$HOST" --port "$PORT"`를 백그라운드 시작한다.
- No-server ready/cleanup 근거: `e2e/start-server.sh:16-26`의 healthcheck는 `HEALTH_URL`이 HTTP 200을 반환할 때만 성공한다. `e2e/start-server.sh:73-91`은 최대 `WAIT_SECONDS` 동안 1초 간격으로 healthcheck를 반복하고, 서버 조기 종료나 timeout이면 실패한다. `e2e/start-server.sh:29-37` 및 `e2e/start-server.sh:57-59`는 wrapper가 시작한 `SERVER_PID`를 종료하고 `TMP_DIR`를 삭제하도록 EXIT/INT/TERM trap을 둔다.
- Existing-server 경로 근거: `e2e/start-server.sh:50-53`은 wrapper 시작 직후 healthcheck가 성공하면 기존 서버를 재사용하고 `run_tests "$@"`만 실행한 뒤 그 종료 코드로 종료한다. 이 분기는 `SERVER_PID`와 cleanup trap을 설정하기 전이므로 기존 서버를 kill하지 않는다. 재사용 판단은 포트 점유가 아니라 `e2e/start-server.sh:16-26`의 `/healthz` HTTP 200 응답이다.
- Playwright config 근거: `e2e/playwright.config.mjs:20`은 기본 baseURL을 `http://127.0.0.1:8879`로 둔다. `e2e/playwright.config.mjs:25-37`은 같은 포트의 webServer URL과 `reuseExistingServer: true`를 설정해 wrapper가 띄운 서버나 기존 healthy 서버를 재사용할 수 있게 한다. `e2e/playwright.controller.config.mjs`와 `e2e/playwright.sqlite.config.mjs`는 별도 포트/타겟 설정이며 `Makefile:12-13`의 기본 `e2e-test` 직접 경로는 아니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `11a7507190024a3f6e2d9df663d39edaad4ef4ab3a7cbe4dfc198ef912caf5a5`로 요청 handoff SHA와 일치.
- `ls e2e/start-server.sh` 통과: 파일 존재 확인.
- `grep -n "e2e-test\|start-server\|SMOKE_PORT\|healthcheck" Makefile | head -20` 실행: `e2e-test`가 `e2e/start-server.sh`를 호출함을 확인. `SMOKE_PORT`는 Makefile에 없었다.
- `bash -n e2e/start-server.sh` 통과, 출력 없음.
- `nl -ba Makefile`, `nl -ba e2e/start-server.sh`, `nl -ba e2e/playwright.config.mjs`, `nl -ba e2e/playwright.controller.config.mjs`, `nl -ba e2e/playwright.sqlite.config.mjs`로 정적 코드 근거를 확인했다.
- `git status --short -- work/4/26/2026-04-26-e2e-healthcheck-wrapper-audit.md Makefile e2e/start-server.sh e2e/playwright.config.mjs e2e/playwright.controller.config.mjs e2e/playwright.sqlite.config.mjs` 실행 시 읽기 전용 대상 변경 없음과 신규 closeout 파일 미존재를 확인한 뒤 작성했다.
- `git diff --check -- work/4/26/2026-04-26-e2e-healthcheck-wrapper-audit.md` 통과, 출력 없음.
- Playwright live 실행은 handoff의 sandbox 제약과 범위 제한에 따라 수행하지 않았다. `make e2e-test`, `cd e2e && npm test`, `npx playwright test`는 실행하지 않았다.

## 남은 리스크
- 이번 결론은 정적 코드 감사 기준이다. 실제 no-server / existing-server live 경로의 브라우저 실행 성공 여부는 확인하지 않았다.
- 기존 healthy 서버가 `/healthz` HTTP 200은 반환하지만 Playwright 기본 baseURL 경로가 정상 응답하지 않는 비정상 상태까지는 이 정적 감사만으로 보장하지 않는다.
- `e2e/playwright.sqlite.config.mjs`의 sqlite smoke 경로는 기본 `make e2e-test` 경로와 별도 설정이므로 이번 release gate truth의 직접 대상에서 제외했다.
- 기존 작업트리의 untracked `report/gemini/**` 파일들은 이번 handoff 범위 밖이므로 수정하지 않았다.
- commit, push, branch/PR 생성, merge는 수행하지 않았다.
