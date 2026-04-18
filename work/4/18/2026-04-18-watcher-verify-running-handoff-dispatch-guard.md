# 2026-04-18 watcher verify-running handoff dispatch guard

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`

## 사용 skill
- `work-log-closeout`: `/work` closeout 형식과 필수 사실 항목을 current repo 규칙에 맞춰 정리하기 위해 사용했습니다.
- `release-check`: 마무리 단계에서 실제 실행한 검증과 문서 동기화 범위를 과장 없이 점검하기 위해 사용했습니다.

## 변경 이유
- 최신 Claude handoff가 이미 `STATUS: implement`로 올라와 있었는데도 Claude pane이 바로 새 작업을 받지 못하고, `slot_verify` lease TTL이 끝날 때까지 idle prompt에 머무는 지연이 있었습니다.
- 원인을 추적해 보니 watcher가 current run의 `VERIFY_RUNNING` job을 끝까지 계속 step하지 않고, poll마다 "최신 미검증 `/work` 1개"만 다시 고르면서 오래된 `work/4/9/...` note를 새 verify 후보로 끼워 넣고 있었습니다.
- 그 결과 current verify round가 `VERIFY_DONE`로 닫히지 못해 lease release와 pending Claude handoff 반영이 늦어졌고, runtime status도 stale pending round를 current truth처럼 섞어 보이게 됐습니다.

## 핵심 변경
- `watcher_core.py`에 current run watcher state를 읽는 `_get_current_run_jobs(...)` helper를 추가했습니다.
- `WatcherCore._poll()`에서 work 디렉터리의 새 artifact를 고르기 전에 current run의 `VERIFY_RUNNING` job이 남아 있는지 먼저 확인하고, 있으면 그 job들을 우선 `self.sm.step(...)`으로 계속 진행하도록 바꿨습니다.
- active verify job을 step한 뒤에는 `_flush_pending_claude_handoff()`를 즉시 다시 태워, verify close가 끝난 같은 polling cycle 안에서 pending Claude handoff가 release될 수 있게 맞췄습니다.
- `.pipeline/README.md`에 current run `VERIFY_RUNNING` job이 살아 있는 동안 watcher는 그 round를 terminal close 또는 재큐잉까지 계속 step하고, 그 사이 오래된 다른 unverified `/work`가 lease release나 pending handoff를 가리면 안 된다는 계약을 추가했습니다.
- `tests/test_watcher_core.py`에 회귀 테스트를 추가해, in-flight verify job이 `VERIFY_DONE`로 닫히고 Claude turn이 release되기 전에 오래된 stale `/work`가 새 verify candidate로 state에 생기지 않는 흐름을 고정했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.ClaudeHandoffDispatchTest tests.test_watcher_core.VerifyCompletionContractTest`
  - 결과: `Ran 17 tests`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과

## 남은 리스크
- 이번 수정은 current run의 `VERIFY_RUNNING` round를 우선 추적하도록 막았지만, 오래된 unmatched `/work` note를 언제 다시 verify 대상으로 승격할지에 대한 장기 정책까지 정리한 것은 아닙니다.
- supervisor `active_round` surface는 여전히 state 파일의 최신 `updated_at` 중심으로 고르므로, 향후 stale pending job이 current surface를 혼동시키는 다른 경로가 보이면 별도 round-selection 보정이 필요할 수 있습니다.
- 이번 라운드는 watcher contract fix와 focused unit regression만 확인했습니다. 실제 tmux live runtime에서 같은 incident family가 완전히 사라졌는지까지는 별도 session replay나 launcher smoke로 추가 확인하는 편이 맞습니다.
