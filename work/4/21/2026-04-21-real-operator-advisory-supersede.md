# 2026-04-21 real operator advisory supersede

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-real-operator-advisory-supersede.md`

## 사용 skill
- `security-gate`: commit/push 승인 같은 real operator boundary가 자동 advisory 루프로 숨지 않는지 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 기준으로 closeout을 남겼습니다.

## 변경 이유
- 스크린샷에서 `.pipeline/gemini_advice.md`의 `RECOMMEND: needs_operator (C) ... 커밋/푸시 승인`이 계속 살아 보여, operator-only 승인 경계가 advisory 선택 루프처럼 보였습니다.
- 실제 active control은 더 높은 `CONTROL_SEQ`의 `.pipeline/operator_request.md`였지만, 이전 `gemini_request.md` / `gemini_advice.md`가 `STATUS: request_open` / `STATUS: advice_ready`로 남아 운영자와 UI에 혼선을 만들 수 있었습니다.

## 핵심 변경
- real operator boundary가 active current truth가 되면 더 낮은 `CONTROL_SEQ`의 `.pipeline/gemini_request.md` / `.pipeline/gemini_advice.md`를 `STATUS: superseded`로 rewrite하도록 watcher에 공용 helper를 추가했습니다.
- superseded slot에는 `SUPERSEDED_BY`, `SUPERSEDED_BY_SEQ`, `SUPERSEDED_REASON` header를 남기고, watcher raw log와 runtime event에 `advisory_slot_superseded`를 남기게 했습니다.
- startup `OPERATOR_WAIT`와 rolling `operator_request_pending` 양쪽에서 같은 helper를 호출하게 해, 재시작 후에도 stale advisory가 다시 pending처럼 보이지 않게 했습니다.
- `tests.test_watcher_core`에 real operator stop seq 30이 stale advisory seq 28/29를 supersede하는 회귀 테스트를 추가했습니다.
- `.pipeline/README.md`, runtime 기술설계, 운영 RUNBOOK에 superseded advisory slot 운영 규칙을 동기화했습니다.
- live runtime에서 기존 seq 686/687 `gemini_request.md` / `gemini_advice.md`가 `SUPERSEDED_BY_SEQ: 690`으로 중립화된 것을 확인했습니다.

## 검증
- `python3 -m py_compile watcher_core.py` → 통과
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest.test_real_operator_boundary_supersedes_lower_seq_advisory_slots` → 1 test OK
- `python3 -m unittest tests.test_watcher_core` → 163 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_launcher tests.test_pipeline_gui_home_presenter` → 164 tests OK
- `git diff --check watcher_core.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` → 통과
- live 확인: `.pipeline/gemini_request.md` seq 686과 `.pipeline/gemini_advice.md` seq 687이 `STATUS: superseded`, `SUPERSEDED_BY_SEQ: 690`으로 내려갔습니다.
- live 확인: `.pipeline/runs/20260421T101505Z-p460279/status.json`에서 `runtime_state=RUNNING`, watcher `alive=true`, `turn_state=OPERATOR_WAIT`, active control seq 690 `needs_operator`, `automation_reason_code=approval_required`, `automation_next_action=operator_required`를 확인했습니다.

## 남은 리스크
- 현재 live stop은 자동화 루프가 아니라 dirty worktree commit/push 승인이라는 실제 operator boundary입니다. 이 경계는 의도적으로 자동 진행하지 않습니다.
- 이번 helper가 runtime event를 남기도록 보강된 뒤에는 이미 superseded 된 기존 seq 686/687 slot에 대해 새 `events.jsonl` 이벤트를 retroactive로 쓰지는 않았습니다. 해당 실동작 증거는 `.pipeline/logs/experimental/raw.jsonl`의 `advisory_slot_superseded` 두 줄과 slot header에 남아 있습니다.
- `python3 -m pipeline_runtime.cli status ...`와 `jq`는 이 환경에서 각각 status subcommand 부재, `jq` 미설치로 사용할 수 없었습니다. live 상태 확인은 generated `status.json`과 shell text inspection으로 대체했습니다.
