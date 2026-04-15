## 변경 파일
- AGENTS.md
- CLAUDE.md
- GEMINI.md
- PROJECT_CUSTOM_INSTRUCTIONS.md
- work/README.md
- verify/README.md
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md
- pipeline_runtime/supervisor.py
- watcher_core.py
- tests/test_pipeline_runtime_supervisor.py

## 사용 skill
- doc-sync

## 변경 이유
- 실제 운영 중 Codex가 다음 exact slice를 아직 못 좁힌 상황에서 바로 `.pipeline/operator_request.md`로 서는 흐름이 보였습니다.
- 이 경우는 real operator-only decision이 아니라 next-slice ambiguity에 가까워서, 문서 기준 canonical flow대로라면 Gemini arbitration을 먼저 거쳐야 합니다.
- 기존 규칙은 대체로 그 방향을 암시했지만, mirror 문서와 runtime prompt가 모두 같은 강도로 고정되어 있지는 않아 다시 드리프트할 여지가 있었습니다.

## 핵심 변경
- operator policy mirror를 동기화했습니다.
  - Codex는 next-slice ambiguity, overlapping candidates, low-confidence prioritization일 때 `.pipeline/gemini_request.md`를 먼저 여는 쪽으로 명시했습니다.
  - `.pipeline/operator_request.md`는 real operator-only decision, approval/truth-sync blocker, immediate safety stop, 또는 Gemini advice 이후에도 exact slice를 못 좁힌 경우로 한정했습니다.
- runtime prompt를 강화했습니다.
  - `pipeline_runtime/supervisor.py`의 `verify` / `followup` prompt에 Gemini-first arbitration 규칙을 추가했습니다.
  - `watcher_core.py`의 `verify_prompt`, `verify_triage_prompt`, `followup_prompt`에도 같은 규칙을 반영했습니다.
- 회귀 테스트를 추가했습니다.
  - verify prompt가 slice ambiguity에서 Gemini-first를 요구하는지
  - followup prompt가 Gemini advice 이후에만 operator stop을 허용하는지
  를 고정했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`

## 남은 리스크
- 이번 수정은 Codex/Gemini/operator 판단 경계를 prompt + policy contract로 더 단단히 만든 것입니다. 이미 떠 있는 runtime 프로세스에는 재시작 후 반영됩니다.
- 실제 모델 응답은 여전히 prompt 품질의 영향을 받으므로, 이후 live round에서 Gemini-first arbitration이 기대대로 관찰되는지 한 번 더 보는 편이 좋습니다.
- `operator_request`가 정말 operator-only stop으로만 쓰이게 되었는지는 다음 실제 followup round에서 추가 관찰 가치가 있습니다.
