# 2026-05-18 publish held root runtime instruction parity guard

## 변경 파일

- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.claude/rules/pipeline-runtime.md`
- `work/5/18/2026-05-18-publish-held-root-runtime-instruction-parity-guard.md`

## 사용 skill

- `doc-sync`: root 운영 문서와 `.claude/rules/pipeline-runtime.md`의 publish-held/operator-retriage 및 dispatcher runtime-status 규칙을 동기화하는 데 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검사, 남은 리스크를 표준 `/work` 형식으로 남기는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1910` handoff는 `CONTROL_SEQ: 1909`에서 보강된 runtime/operator 규칙을 root instruction 문서들과 맞추라고 지시했습니다.
- 기존 root 문서에는 publish-held/operator-retriage 경계가 일부 있었지만, `RUNTIME_STATUS_AT_DISPATCH`를 lane-local `status --json`, `doctor --json`, tmux 접근 충돌보다 우선하는 runtime-liveness 표면으로 취급한다는 규칙은 빠져 있었습니다.
- `.claude/rules/pipeline-runtime.md`에는 이미 두 규칙이 추가된 상태였으므로, `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 같은 고위험 운영 경계를 최소 문장으로 반영했습니다.

## 핵심 변경

- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 verify/retriage prompt의 `RUNTIME_STATUS_AT_DISPATCH`를 dispatcher runtime-liveness 권위 표면으로 취급하는 규칙을 추가했습니다.
- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`의 publish-held 문구에 `PUBLISH_HELD: true` recovery는 publication을 보류하고 다음 non-publish local control을 써야 한다는 표현을 명시했습니다.
- `.claude/rules/pipeline-runtime.md`의 기존 `CONTROL_SEQ: 1909` 변경과 root 문서 표현이 같은 운영 경계를 가리키도록 맞췄습니다.
- production code, tests, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, stash, commit/push/PR/merge/release 작업은 수행하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 요청된 handoff SHA `7590357ab077cf091da22b8315b97989fb2a3df476c52a91e7e0846b461297c2`와 일치했습니다.
- `rg -n "RUNTIME_STATUS_AT_DISPATCH|runtime_status_at_dispatch|lane-local|lane_local|commit_push_bundle_authorization|PUBLISH_HELD|publish backlog|ADVISORY_DISABLED" AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md`
  - 통과. root 문서들과 `.claude/rules/pipeline-runtime.md`에서 publish-held/operator-retriage 및 dispatcher runtime-status 규칙이 확인됐습니다.
- `git status --short -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-root-runtime-instruction-parity-guard.md`
  - closeout 작성 전 기준 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.claude/rules/pipeline-runtime.md`가 modified 상태임을 확인했습니다.
- `git diff --check -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-root-runtime-instruction-parity-guard.md`
  - closeout 작성 전 기준 출력 없이 통과했습니다.
- `git diff -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md`
  - 통과. root instruction parity와 `.claude` runtime rule 요약 변경만 확인했습니다.
- `rg -n "RUNTIME_STATUS_AT_DISPATCH|runtime_status_at_dispatch|lane-local|lane_local|commit_push_bundle_authorization|PUBLISH_HELD|publish backlog|ADVISORY_DISABLED" AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md`
  - closeout 작성 후 기준 통과. 네 문서에서 필요한 운영 규칙 표면을 다시 확인했습니다.
- `git status --short -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-root-runtime-instruction-parity-guard.md`
  - closeout 작성 후 기준 네 문서 modified와 새 `/work` closeout untracked만 표시했습니다.
- `git diff --check -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-root-runtime-instruction-parity-guard.md`
  - closeout 작성 후 기준 출력 없이 통과했습니다.
- `git status --short -- .pipeline/advisory_request.md .pipeline/operator_request.md .pipeline/implement_handoff.md`
  - 통과. 이번 implement 라운드에서 control slot 변경은 없었습니다.
- `git diff --stat -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .claude/rules/pipeline-runtime.md work/5/18/2026-05-18-publish-held-root-runtime-instruction-parity-guard.md`
  - 통과. 추적 파일 기준 `4 files changed, 20 insertions(+), 6 deletions(-)`로 확인했습니다.

## 남은 리스크

- 전체 unittest, Playwright, `make e2e-test`, local socket/server startup, live tmux E2E, long soak는 실행하지 않았습니다. 이번 handoff는 root instruction docs parity 작업이며 production code/test 변경을 하지 않았기 때문입니다.
- dirty tracked source/test 7개 파일은 이번 라운드에서 수정하거나 분리하지 않았습니다.
- `stash@{0}`는 적용/삭제/검증하지 않았습니다.
- publication은 계속 held 상태입니다. commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication, readiness claim은 수행하지 않았습니다.
