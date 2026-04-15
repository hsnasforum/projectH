# Pipeline Runtime synthetic receipt stall fix

## 변경 파일
- watcher_core.py
- tests/test_watcher_core.py
- report/pipeline_runtime/verification/2026-04-13-synthetic-receipt-stall-smoke.md

## 사용 skill
- 없음

## 변경 이유
- 24시간 synthetic-soak가 `receipt_count=1`에서 멈춘 원인을 확인한 결과, watcher가 Claude pane에 출력된 implement prompt 내부의 `BLOCKED_SENTINEL` 예시 텍스트를 실제 `implement_blocked` 응답으로 오탐했습니다.
- 그 결과 Claude active turn에서 `/work` snapshot diff를 통한 다음 verify round 개시가 막혀 synthetic workload가 첫 receipt 이후 진행되지 않았습니다.

## 핵심 변경
- `watcher_core._extract_claude_implement_blocked_signal()`에 prompt-template sentinel 예시를 무시하는 가드를 추가했습니다.
- `BLOCKED_SENTINEL:` 또는 `emit the exact sentinel below` 직후의 `STATUS: implement_blocked`는 실제 blocked signal로 처리하지 않도록 했습니다.
- placeholder 값(`<short_reason>`)에서 파생된 `BLOCK_REASON` / `BLOCK_ID`도 sentinel로 인정하지 않도록 막았습니다.
- watcher 회귀 테스트에 prompt-template false positive 케이스를 추가했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
- `python3 -m unittest -v tests.test_watcher_core.ClaudeImplementBlockedTest`
- `python3 scripts/pipeline_runtime_gate.py --mode experimental synthetic-soak --duration-sec 90 --sample-interval-sec 2 --min-receipts 3 --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-13-synthetic-receipt-stall-smoke.md`
- synthetic smoke 결과:
  - `receipt_count=4`
  - `degraded_counts={}`
  - `broken_seen=False`
  - `duplicate_dispatch_count=0`
  - `control_mismatch_max_streak=0`

## 남은 리스크
- 이번 검증은 90초 synthetic-smoke까지 재확인한 상태이며, 최종 채택 기준의 24시간 synthetic-soak는 패치 반영 상태로 다시 1회 실행해 확인해야 합니다.
- Claude blocked 감지는 prompt-template 오탐은 막았지만, 다른 형태의 vendor pane formatting 변화에 따른 soft-signal 오탐 가능성은 여전히 장기 soak에서 계속 관찰이 필요합니다.
