# Pipeline Runtime Gemini readiness stall fix

## 변경 파일
- watcher_core.py
- tests/test_watcher_core.py
- report/pipeline_runtime/verification/2026-04-14-gemini-readiness-synthetic-smoke.md
- report/pipeline_runtime/verification/2026-04-14-gemini-readiness-synthetic-pass.md
- report/pipeline_runtime/progress/2026-04-14-gemini-readiness-stall-fix.md

## 사용 skill
- 없음

## 변경 이유
- 24시간 synthetic-soak가 살아 있는 것처럼 보이지만 실제로는 `CONTROL_SEQ=5`의 `.pipeline/gemini_request.md` 이후 더 진행되지 않고 멈췄습니다.
- 확인 결과 watcher dispatch readiness가 tmux pane의 전통적인 prompt glyph(`>`, `›`, `❯`, `$`)만 입력 가능 상태로 인정하고, synthetic Gemini lane의 텍스트형 ready 화면(`Gemini CLI`, `Type your message`, `workspace`)은 준비 완료로 보지 못했습니다.
- 그 결과 Gemini pane은 실제로는 입력 가능했지만 watcher가 `notify_gemini`를 timeout 처리했고, `gemini_advice -> 다음 handoff -> 다음 receipt`가 이어지지 않았습니다.

## 핵심 변경
- `watcher_core._pane_text_has_gemini_ready_prompt()`를 추가해 Gemini의 텍스트형 ready 화면을 readiness 신호로 인정하도록 보강했습니다.
- `watcher_core._pane_text_has_input_cursor()`가 기존 glyph prompt가 없더라도 Gemini ready 텍스트를 보면 입력 가능 상태로 반환하도록 수정했습니다.
- watcher 회귀 테스트에 Gemini 텍스트 ready prompt 양성/음성 케이스를 추가했습니다.
- synthetic smoke를 다시 돌려 `gemini_request -> gemini_advice -> claude_handoff` 전이가 실제로 복구됐는지 확인했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
- `python3 -m unittest -v tests.test_watcher_core.PanePromptDetectionTest tests.test_watcher_core.ClaudeImplementBlockedTest`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental synthetic-soak --duration-sec 180 --sample-interval-sec 2 --min-receipts 6 --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-14-gemini-readiness-synthetic-smoke.md`
- 180초 synthetic smoke 관찰 결과:
  - `receipt_count=5`
  - `broken_seen=False`
  - `degraded_counts={}`
  - retained workspace event 확인:
    - `CONTROL_SEQ=5 request_open`
    - `CONTROL_SEQ=6 advice_ready`
    - `CONTROL_SEQ=7 implement`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental synthetic-soak --duration-sec 200 --sample-interval-sec 2 --min-receipts 5 --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-14-gemini-readiness-synthetic-pass.md`
- 200초 synthetic smoke 결과:
  - `receipt_count=5`
  - `broken_seen=False`
  - `degraded_counts={}`
  - `duplicate_dispatch_count=0`
  - `control_mismatch_max_streak=0`

## 남은 리스크
- 이미 멈춘 기존 24시간 synthetic-soak 프로세스는 패치 전 코드로 시작된 런이라 이 수정이 hot-reload되지 않습니다. 그 런은 성공으로 간주할 수 없고, 패치 반영 상태에서 다시 시작해야 합니다.
- 이번 수정은 Gemini readiness 텍스트를 현재 synthetic/vendor 화면에 맞춰 보강한 것입니다. 실제 vendor UI 문구가 다시 바뀌면 wrapper event 기반 readiness로 더 내리는 추가 보강이 여전히 필요합니다.
