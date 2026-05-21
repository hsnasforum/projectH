STATUS: verified
WORK: work/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md
PREVIOUS_VERIFY: verify/5/19/2026-05-19-publish-held-prompt-runtime-non-socket-aggregate-guard.md
CONTROL_SEQ_NEXT: 1992
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md`의 tmux
literal fallback repair를 현재 작업트리에서 확인했습니다.
`watcher_dispatch._send_literal_text_to_pane()`는 이제 `tmux send-keys`
literal chunk 앞에 `--` option terminator를 넣습니다. 새 테스트는 chunk가
`-`로 시작해도 tmux 옵션으로 해석되지 않는 호출 형태를 고정합니다.

추가 runtime 관찰도 확인했습니다. 수정 뒤 live watcher가 재시작했고, 기존
`codex_verify_dispatch_failure_loop` pending job은 matching verify note를
확인한 뒤 `matching_verify_already_exists` 사유로 archive됐습니다. 최신 status는
`runtime_state=RUNNING`, `degraded_reason=""`, Codex lane `READY`입니다.

## 사용 skill

- `round-handoff`: repair `/work`와 실제 테스트 결과를 재확인했습니다.
- `security-gate`: tmux shell dispatch 호출이 새 권한, 자동 승인, 외부
  publication으로 확장되지 않는지 확인했습니다.
- `finalize-lite`: 구현 closeout, 검증, 남은 리스크, doc-sync 필요 여부를
  점검했습니다.

## 확인한 대상

- `AGENTS.md`
- `.agents/skills/security-gate/SKILL.md`
- `.agents/skills/finalize-lite/SKILL.md`
- `.agents/skills/work-log-closeout/SKILL.md`
- `work/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md`
- `verify/5/19/2026-05-19-publish-held-prompt-runtime-non-socket-aggregate-guard.md`
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `.pipeline/runs/20260520T041821Z-p1140/status.json`
- `.pipeline/logs/experimental/watcher.log`

## 실행한 검증

- `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.VerifyPendingBackoffTest`
  - 결과: PASS. `Ran 32 tests in 6.533s`, `OK`.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS, 출력 없음.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py verify/5/19/2026-05-19-publish-held-prompt-runtime-non-socket-aggregate-guard.md work/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md`
  - 결과: PASS, 출력 없음.

## 실행하지 않은 검증

- `make controller-test`, Playwright, `make e2e-test`, controller startup,
  local socket probe, end-to-end live dispatch replay, long soak는 실행하지
  않았습니다.
- 이유: 이번 repair는 tmux `send-keys` argument construction의 작은 local
  fix이며, browser-visible contract나 release readiness를 주장하지 않습니다.

## 변경 파일

- `verify/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md`

## 판정

- `VERIFY_DONE`.
- `codex_verify_dispatch_failure_loop`의 직접 원인이던 dash-leading literal
  chunk tmux option parsing 위험은 코드와 테스트로 막았습니다.
- live status는 `needs_operator`에서 벗어나 `RUNNING`으로 돌아왔지만,
  broad runtime/controller smoke는 아직 실행하지 않았습니다.

## 다음 컨트롤 판단

COUNCIL_DECISION: implement
REASON_CODE: publish_held_codex_literal_fallback_runtime_resume_sanity
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 1992

EVIDENCE:
- `work/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md`
- `verify/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md`
- `.pipeline/runs/20260520T041821Z-p1140/status.json`
- `.pipeline/logs/experimental/watcher.log`
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`

REJECTED:
- operator_required: current status no longer reports
  `codex_verify_dispatch_failure_loop` as degraded and no destructive,
  auth/credential, approval-record, merge/release, or publication decision is
  required.
- advisory_request: advisory is disabled for this chain.
- commit/push/PR handoff: publication remains held and this is outside
  implement scope.

## 남은 리스크

- Runtime resume is observed but not soak-tested.
- Publication remains held. commit, push, branch/PR publication,
  PR creation/reuse/update, merge, release, external publication은 수행하지
  않았습니다.
