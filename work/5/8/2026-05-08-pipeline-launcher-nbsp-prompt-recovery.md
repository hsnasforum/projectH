# 2026-05-08 pipeline launcher NBSP prompt recovery

## 변경 파일

- `pipeline_runtime/lane_surface.py`
- `tests/test_watcher_core.py`
- generated runtime state: `.pipeline/locks/archive/slot_verify.lock.stale-20260508T0825Z`

## 사용 skill

- `security-gate`: tmux pane 자동 입력 경계와 runtime lock 정리의 승인/감사 경계를 점검했다.
- `finalize-lite`: 변경 파일, 실제 검증, 문서 sync 필요 여부, `/work` closeout 준비 상태를 확인했다.
- `work-log-closeout`: 구현/복구 라운드 종료 기록 형식과 실제 실행 사실 정리에 사용했다.

## 변경 이유

- pipeline launcher가 최신 `/work`를 verify owner에게 넘기지 못하고 `VERIFY_PENDING`에 머물렀다.
- 원인은 Claude Code prompt line의 `❯` 뒤 공백이 일반 space가 아니라 NBSP(`\xa0`)인 경우를 `line_looks_like_input_prompt()`가 ready prompt로 인식하지 못한 것이었다.
- hot reload 중 기존 watcher가 남긴 `slot_verify.lock`이 supervisor-owned active lease로 남아 새 watcher가 TTL 600초를 기다리는 상태도 함께 확인됐다.

## 핵심 변경

- `line_looks_like_input_prompt()`에서 NBSP를 일반 공백으로 정규화한 뒤 prompt 여부를 판정하게 했다.
- `PanePromptDetectionTest`에 `❯\xa0...` 형태의 Claude Code prompt가 idle/ready로 잡히는 회귀 테스트를 추가했다.
- live watcher self-restart가 새 코드를 import한 것을 확인했다.
- dispatch 이벤트 없이 남은 generated lease `.pipeline/locks/slot_verify.lock`은 원본을 `.pipeline/locks/archive/slot_verify.lock.stale-20260508T0825Z`로 보존 이동해 현재 런을 재개시켰다.
- 재개 후 status가 `VERIFY_PENDING`에서 `VERIFYING` / `VERIFY_RUNNING`으로 바뀌고, `%4` Claude pane에 verify prompt가 전달된 것을 확인했다.

## 검증

- `python3 -m py_compile pipeline_runtime/lane_surface.py watcher_dispatch.py watcher_core.py`
  - PASS.
- `python3 -m unittest -v tests.test_watcher_core.PanePromptDetectionTest`
  - PASS: 7개 테스트 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.PipelineRuntimeCliTest tests.test_watcher_core.PanePromptDetectionTest`
  - FAIL: `tests.test_pipeline_runtime_cli`에 `PipelineRuntimeCliTest` 클래스가 없어 명령 대상 지정 오류.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli tests.test_watcher_core.PanePromptDetectionTest`
  - PASS: 39개 테스트 통과.
- `git diff --check -- pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
  - PASS.
- live runtime 확인:
  - watcher self-restart event: `watcher_self_restart_started` / `watcher_self_restart_completed`, 새 watcher PID `64001`.
  - stale lock 보존 이동 후 watcher log: `claude ready output detected after dispatch`, `VERIFY_PENDING -> VERIFY_RUNNING`.
  - status: active round `state=VERIFYING`, `status=VERIFY_RUNNING`, progress `running_verification`.

## 남은 리스크

- 현재 런은 verify owner가 실제 검증을 수행 중인 상태까지 확인했고, verify note 작성 완료까지 기다리지는 않았다.
- 이번 코드 변경은 NBSP prompt 감지에 한정했다. watcher self-restart 중 active lease가 supervisor-owned로 남으면 TTL까지 대기할 수 있는 구조적 리스크는 별도 slice로 남아 있다.
