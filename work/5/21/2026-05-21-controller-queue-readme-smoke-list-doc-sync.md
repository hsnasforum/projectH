# 2026-05-21 controller Queue README smoke list doc sync

## 변경 파일

- `README.md`
- `work/5/21/2026-05-21-controller-queue-readme-smoke-list-doc-sync.md`

## 사용 skill

- `work-log-closeout`: docs-only 구현 라운드의 변경 파일, 실제 검증 결과, 남은 리스크를 `/work` 형식으로 기록하는 데 사용했다.

## 변경 이유

- `.pipeline/implement_handoff.md#2083`은 실제 controller Queue presentation smoke coverage가 `README.md`의 `Current controller smoke scenarios` 목록에 빠져 있는 drift를 README-only로 정리하라고 지시했다.
- `e2e/tests/controller-smoke.spec.mjs`에는 `controller renders Queue presentation from runtime payloads` 시나리오가 있고, Queue row와 `#marquee-text` Queue payload를 확인한다.
- `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/ACCEPTANCE_CRITERIA.md`는 이미 Queue presentation coverage/current contract를 언급하므로 이번 라운드는 제품 spec docs로 확장하지 않는다.

## 핵심 변경

- `README.md`의 `Current controller smoke scenarios` 목록에서 9번 marquee 항목 바로 뒤에 Queue presentation smoke 항목을 추가했다.
- 새 항목은 `/api/runtime/status` Queue payload variants, sidebar `Queue` row text/class, `#marquee-text` Queue payload 확인 범위를 설명한다.
- 뒤따르는 fatigue/lounge scenario 번호를 11-16으로 정리했다.
- 코드, 테스트, fixture, 제품 spec docs, architecture, pipeline runtime, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 변경하지 않았다.
- `README.md`에는 이번 라운드 이전의 다른 dirty hunk가 이미 있었고, 이번 라운드는 controller smoke scenario list hunk만 추가했다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `d955df48bdbbdcc6281d63b4f75af083ca05524676e9caf1c287ad8b35307bdd`와 일치했다.
- `sed -n '474,492p' README.md`
  - 변경 전 확인: `Current controller smoke scenarios` 목록이 9번 marquee 뒤에 바로 10번 fatigue 항목으로 이어져 Queue presentation scenario가 없었다.
- `rg -n "controller renders Queue presentation from runtime payloads|Current controller smoke scenarios:|Queue" README.md e2e/tests/controller-smoke.spec.mjs`
  - 변경 전 확인: 실제 e2e 파일에는 Queue presentation scenario와 helper가 있었지만 README의 controller smoke list에는 같은 scenario명이 없었다.
  - 변경 후 통과: `README.md:484`에 `controller renders Queue presentation from runtime payloads` 항목이 추가됐고, e2e의 `expectQueuePresentation` 및 scenario 위치도 함께 확인됐다.
- `sed -n '690,724p' e2e/tests/controller-smoke.spec.mjs`
  - 통과: 실제 scenario가 Queue payload variants를 순회하며 `expectQueuePresentation()`으로 sidebar Queue row와 marquee Queue text를 확인하는 흐름임을 확인했다.
- `test -e work/5/21/2026-05-21-controller-queue-readme-smoke-list-doc-sync.md; echo $?`
  - 통과: 작성 전 대상 work note가 없었고 결과는 `1`이었다.
- `sed -n '474,493p' README.md`
  - 통과: README 목록에 Queue item이 10번으로 추가됐고 뒤 항목 번호가 11-16으로 정리됐다.
- `git diff --check -- README.md work/5/21/`
  - closeout 작성 전 통과: 출력 없이 종료했다.
  - closeout 작성 후 통과: 출력 없이 종료했다.
- `git status --short -- README.md work/5/21/2026-05-21-controller-queue-readme-smoke-list-doc-sync.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - closeout 작성 전 확인: `README.md`만 modified로 표시됐고 새 work note는 아직 없었다.
  - closeout 작성 후 확인: `README.md`는 modified, 새 work note는 untracked로 표시됐다.

## 남은 리스크

- 이번 라운드는 README-only docs truth-sync라서 unit tests, Playwright, full controller smoke, broad e2e, long soak, socket-bound HTTP, runtime start/stop, `status --json`, `doctor --json`, `tmux` checks는 실행하지 않았다.
- local socket guard family evidence에 따르면 현재 lane의 socket-bound paths는 계속 `local_socket_guard_auto_held`일 수 있으므로, 이 README 수정은 controller-smoke pass나 release readiness claim이 아니다.
- publication은 계속 held 상태이며 commit, push, branch/PR publish, merge, release는 수행하지 않았다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, 다음 handoff/control은 작성하지 않았다.
