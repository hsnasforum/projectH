# 2026-05-21 turn arbitration constant dedup

## 변경 파일
- `pipeline_runtime/turn_arbitration.py`
- `tests/test_turn_arbitration.py`
- `work/5/21/2026-05-21-turn-arbitration-constant-dedup.md`

## 사용 skill
- `security-gate`: turn arbitration 정리가 operator, verify, advisory routing 경계를 완화하지 않고 상수/우선순위 설명 정리에 머무는지 확인하기 위해 사용했습니다.
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `TURN_CLAUDE`, `TURN_CODEX_VERIFY`, `TURN_CODEX_FOLLOWUP`, `TURN_GEMINI`은 canonical turn 상수와 같은 값을 가리키는 vendor-name alias였고, repo 내부 외부 참조가 없었습니다.
- `resolve_watcher_turn()`의 operator recovery/gate 후속 분기는 현재 코드에서 dead code가 아니라 active advisory, verify, releasable handoff 우선순위 이후에 도달하는 fallback입니다.
- alias 중복은 제거하되, B4는 동작 변경 없이 reachability와 우선순위를 테스트와 주석으로 고정하는 것이 이번 slice의 목적이었습니다.

## 핵심 변경
- `pipeline_runtime/turn_arbitration.py`에서 vendor-name turn alias 상수 4개를 삭제했습니다.
- canonical 상수(`TURN_IMPLEMENT`, `TURN_VERIFY`, `TURN_VERIFY_FOLLOWUP`, `TURN_OPERATOR`, `TURN_ADVISORY`, `TURN_IDLE`) 이름과 값은 변경하지 않았습니다.
- `resolve_watcher_turn()`의 operator recovery/gate fallback 앞에 active work 우선순위 뒤에 평가된다는 주석을 추가했습니다.
- `tests/test_turn_arbitration.py`에 canonical-to-legacy label 회귀 테스트를 추가했습니다.
- operator recovery marker와 operator gate marker가 실제로 followup fallback에 도달하는 케이스, 그리고 verify need가 operator recovery marker보다 우선하는 케이스를 추가했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/turn_arbitration.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_turn_arbitration -v`
  - 결과: `Ran 16 tests in 0.002s`, `OK`.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: `Ran 221 tests in 2.670s`, `OK`.
- 확인: `grep -rn "TURN_CLAUDE\|TURN_CODEX_VERIFY" pipeline_runtime/ watcher_core.py watcher_dispatch.py`
  - 결과: match 없음, `grep` 종료코드 1.
- 확인: `grep -rn "TURN_CLAUDE\|TURN_CODEX_VERIFY\|TURN_CODEX_FOLLOWUP" pipeline_runtime/ watcher_core.py watcher_dispatch.py`
  - 결과: match 없음, `grep` 종료코드 1.
- 통과: `git diff --check -- pipeline_runtime/turn_arbitration.py`
  - 결과: PASS, 출력 없음.
- 통과: `git diff --check -- pipeline_runtime/turn_arbitration.py tests/test_turn_arbitration.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- B4는 dead code 제거가 아니라 dead code가 아닌 것으로 확인된 fallback 경로의 주석/테스트 고정으로 처리했습니다.
- `supervisor.py`, `watcher_core.py`, `watcher_dispatch.py` 동작은 이번 slice에서 변경하지 않았습니다.
- 전체 repo unittest discover, browser/E2E, live runtime/tmux 검증은 실행하지 않았습니다.
- 현재 worktree에는 이전 Claude print JSONL lane integration 변경 및 여러 untracked `work/`, `verify/`, `report/gemini/` 기록 파일이 남아 있습니다. 이번 slice에서는 관련 없는 기존 변경을 되돌리거나 포함하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
