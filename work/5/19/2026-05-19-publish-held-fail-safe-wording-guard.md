# 2026-05-19 publish held fail-safe wording guard

## 변경 파일

- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/19/2026-05-19-publish-held-fail-safe-wording-guard.md`

## 사용 skill

- `work-log-closeout`: handoff #1964의 docs-only 문구 정정 범위, 실제 확인 명령, publication hold 상태, 남은 리스크를 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1964`가 `PUBLISH_HELD: true` 상태에서 operator-stop metadata fallback 문구가 외부 commit/push/PR publication 실행처럼 읽히는 위험을 닫으라고 지시했습니다.
- 기존 문서 두 곳에 `fail-safe로 즉시 publish` 표현이 남아 있어, 구조화 metadata가 없거나 알 수 없는 경우의 안전 동작을 `needs_operator` / operator wait로 fail-closed하는 의미로 명확히 바꿨습니다.
- 이번 라운드는 docs-only wording guard이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`의 운영 원칙 7번을 `fail-closed`로 즉시 `needs_operator` / operator wait에 남긴다고 정정했습니다.
- `.pipeline/README.md`의 operator stop publish/gate 판정 문구를 `needs_operator` operator stop surface로 정정했습니다.
- 두 문서 모두 외부 publication 실행으로 해석하지 않는다는 문장을 추가해 operator stop surfacing과 실제 publish 실행을 분리했습니다.
- source/runtime/test 코드는 수정하지 않았습니다.

## 검증

- `rg -n "fail-safe로 즉시 publish|fail-safe.*publish" .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 수정 전 stale wording 2곳을 확인했습니다.
- `if rg -n "fail-safe로 즉시 publish|fail-safe.*publish" .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md; then exit 1; fi`
  - 통과: 수정 후 동일 stale wording이 남지 않았습니다.
- `git diff --check -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-publish-held-fail-safe-wording-guard.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 문서 문구 정정만 수행했으며 broad unittest, Playwright/E2E, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
