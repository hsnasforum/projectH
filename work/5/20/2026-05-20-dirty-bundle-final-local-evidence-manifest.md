# 2026-05-20 dirty bundle final local evidence manifest

## 변경 파일

- `work/5/20/2026-05-20-dirty-bundle-final-local-evidence-manifest.md`

## 사용 skill

- `work-log-closeout`: handoff #2029의 dirty bundle evidence manifest를 한국어 `/work`
  closeout 형식으로 남기고, 실제 변경 파일과 실행한 명령, held gate, 남은 리스크를 분리하기 위해 사용했습니다.

## 변경 이유

- dirty bundle은 socket-free compile/unit aggregate와 release-claim truth guard evidence를
  확보했지만, browser/socket/live runtime/release/publication gate는 여전히 held 상태입니다.
- 같은 계열의 docs-only truth-sync가 반복되어 더 좁은 문구 확인 대신, verify/operator 판단에
  필요한 로컬 증거와 미검증 gate를 하나의 manifest로 정리해야 했습니다.
- implement lane은 commit, push, branch/PR publication, merge, release를 수행할 수 없으므로
  publication boundary를 명시적으로 held로 기록했습니다.

## 핵심 변경

- 소스 코드, 제품 문서, 테스트, runtime logic은 수정하지 않았습니다.
- 최신 evidence로 `work/5/20/2026-05-20-dirty-bundle-release-claim-truth-guard.md`,
  `verify/5/20/2026-05-20-dirty-bundle-release-claim-truth-guard.md`,
  `verify/5/20/2026-05-20-tracked-dirty-bundle-non-socket-aggregate-guard.md`를 읽었습니다.
- 현재 claim 가능한 로컬 evidence는 socket-free compile/unit aggregate PASS, tracked dirty
  bundle diff-check PASS, release/browser/socket overclaim 없음입니다.
- claim할 수 없는 gate는 Playwright, controller smoke, socket-bound HTTP, live runtime
  recovery, release readiness, publication approval입니다.
- publication은 `PUBLISH_HELD: true` 상태로 유지했습니다. commit/push/branch publication/PR/merge/release는 실행하지 않았습니다.
- manifest 작성 직전 dirty tree 요약은 `26 M`, `145 ??`였습니다.

## 로컬 evidence manifest

### 지금 claim 가능한 것

- `verify/5/20/2026-05-20-tracked-dirty-bundle-non-socket-aggregate-guard.md` 기준:
  - tracked dirty bundle은 socket-free compile/unit aggregate evidence를 확보했습니다.
  - work-note truth 기준으로 `431 tests` PASS가 기록되어 있습니다.
  - 해당 verify는 Playwright, controller smoke, socket-bound HTTP, live runtime recovery,
    release readiness를 주장하지 않는다고 기록했습니다.
- `work/5/20/2026-05-20-dirty-bundle-release-claim-truth-guard.md` 및 최신 verify 기준:
  - dirty docs와 최신 work/verify notes에서 full-smoke pass, browser pass, live-runtime
    recovered, release-ready, publication-approved로 과장한 직접 evidence는 확인되지 않았습니다.
  - `README.md`의 controller smoke hit는 scenario 목록이며 PASS 또는 release-ready claim이 아닙니다.
  - `docs/PRODUCT_SPEC.md`의 `recovered` hit는 recurrence-key 설명 문맥이며 live runtime
    recovery claim이 아닙니다.
  - `local_socket_guard_auto_held`는 environment-held verify follow-up으로 기록되어 있습니다.

### 계속 held 또는 unverified인 것

- Playwright browser smoke는 이번 slice에서 실행하지 않았고 PASS로 주장하지 않습니다.
- controller smoke, full `make e2e-test`, release smoke, long soak는 실행하지 않았고 PASS로 주장하지 않습니다.
- socket-bound HTTP 테스트와 live runtime recovery는 `local_socket_guard_auto_held` 및 dispatcher
  surface의 `STARTING/recovering/retrying` 맥락 때문에 release-ready evidence로 보지 않습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 실행하지 않았고 승인된 것으로 기록하지 않습니다.

### dirty tree 요약

- `git status --short --untracked-files=all | awk '{print $1}' | sort | uniq -c`
  - 결과: `26 M`, `145 ??`였습니다. 이 값은 이 manifest 작성 직전의 표본입니다.
- `git diff --name-status`
  - 결과: tracked modified paths는 26개였습니다.
  - 주요 범위: `.pipeline/README.md`, `README.md`, `app/`, `docs/`, `e2e/tests/web-smoke.spec.mjs`,
    `pipeline_runtime/`, `tests/`, `verify_fsm.py`, `watcher_core.py`, `watcher_dispatch.py`,
    `watcher_prompt_assembly.py`.
- `find work/5/20 -maxdepth 1 -type f | sort | tail -n 12`
  - 결과: lexicographic tail에 runtime/stale/reviewed-memory/tracked dirty bundle work notes가 포함되었습니다.
- `find verify/5/20 -maxdepth 1 -type f | sort | tail -n 12`
  - 결과: lexicographic tail에 runtime/stale/reviewed-memory/tracked dirty bundle verify notes가 포함되었습니다.
- `ls -t work/5/20 | head -6`
  - 결과: 최신 mtime 기준 work note는 `2026-05-20-dirty-bundle-release-claim-truth-guard.md`였습니다.

## 검증

- `sed -n '1,260p' AGENTS.md`
  - 결과: PASS. local-first, approval-based, implement owner boundary, no publish 원칙을 확인했습니다.
- `sed -n '1,220p' .pipeline/harness/implement.md`
  - 결과: PASS. implement owner는 active handoff 하나만 실행하고 `/work` closeout 후 멈추는 역할임을 확인했습니다.
- `sed -n '1,240p' .pipeline/implement_handoff.md`
  - 결과: PASS. `CONTROL_SEQ: 2029`, evidence manifest, `PUBLISH_HELD: true`, no publish 지시를 확인했습니다.
- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `4dfa37a8617e6f468f7f40e038ebd3e436a6cf6fa41ae0184024bc6b6d3e1161`와 일치했습니다.
- `sed -n '1,220p' .agents/skills/work-log-closeout/SKILL.md`
  - 결과: PASS. `/work` closeout 표준 섹션과 실행 사실 기록 규칙을 확인했습니다.
- `sed -n '1,260p' work/5/20/2026-05-20-dirty-bundle-release-claim-truth-guard.md`
  - 결과: PASS. release/browser/socket truth guard closeout과 남은 held gate를 확인했습니다.
- `sed -n '1,280p' verify/5/20/2026-05-20-dirty-bundle-release-claim-truth-guard.md`
  - 결과: PASS. 최신 verify가 direct false overclaim 없음, release/browser/socket/live/publication held를 기록했음을 확인했습니다.
- `sed -n '1,260p' verify/5/20/2026-05-20-tracked-dirty-bundle-non-socket-aggregate-guard.md`
  - 결과: PASS. socket-free aggregate evidence와 held browser/socket/release gate를 확인했습니다.
- `git status --short --untracked-files=all | awk '{print $1}' | sort | uniq -c`
  - 결과: PASS. manifest 작성 직전 상태는 `26 M`, `145 ??`였습니다.
- `git diff --name-status`
  - 결과: PASS. tracked modified paths 26개를 확인했습니다.
- `find work/5/20 -maxdepth 1 -type f | sort | tail -n 12`
  - 결과: PASS. handoff가 요청한 work note 표본을 확인했습니다.
- `find verify/5/20 -maxdepth 1 -type f | sort | tail -n 12`
  - 결과: PASS. handoff가 요청한 verify note 표본을 확인했습니다.
- `test -e work/5/20/2026-05-20-dirty-bundle-final-local-evidence-manifest.md; echo $?`
  - 결과: PASS. manifest 작성 전 대상 파일 없음(`1`)을 확인했습니다.
- `ls -t work/5/20 | head -6`
  - 결과: PASS. 최신 mtime 기준 work note를 확인했습니다.
- `git diff --check -- work/5/20/2026-05-20-dirty-bundle-final-local-evidence-manifest.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-dirty-bundle-final-local-evidence-manifest.md`
  - 결과: PASS. 새 파일 비교라 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- 이번 handoff는 evidence manifest 작성이므로 unit, Playwright, controller smoke, full
  `make e2e-test`, release smoke, long soak, socket-bound HTTP 테스트는 실행하지 않았습니다.
- `python3 -m pipeline_runtime.cli start ...`, `tmux`, lane-local `status --json`,
  `doctor --json`는 실행하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.
- dirty tree는 여전히 크며, 이 manifest는 release readiness나 publication approval이 아닙니다.
