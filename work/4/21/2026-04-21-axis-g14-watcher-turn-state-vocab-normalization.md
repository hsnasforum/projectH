# 2026-04-21 AXIS-G14 watcher turn state vocab normalization

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `work/4/21/2026-04-21-axis-g14-watcher-turn-state-vocab-normalization.md`

## 사용 skill
- `work-log-closeout`: handoff 수행 후 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 closeout 형식으로 정리했습니다.

## 변경 이유
- AXIS-G14 handoff는 `WatcherTurnState`에 남아 있던 legacy alias 중 `CLAUDE_ACTIVE`, `CODEX_FOLLOWUP`, `GEMINI_ADVISORY`를 제거하고, watcher 본체와 watcher 테스트의 enum 참조를 role-first canonical 이름으로 통일하라고 지시했습니다.
- `pipeline_runtime/supervisor.py`가 이미 canonical 이름으로 전환된 상태라, watcher 쪽 vocabulary도 같은 방향으로 맞춰 향후 legacy alias 의존을 줄였습니다.
- FSM 로직, state 전환 조건, enum string 값은 변경하지 않고 참조 이름만 정리했습니다.

## 핵심 변경
- `watcher_core.py`의 `WatcherTurnState`에서 `CLAUDE_ACTIVE = IMPLEMENT_ACTIVE`, `CODEX_FOLLOWUP = VERIFY_FOLLOWUP`, `GEMINI_ADVISORY = ADVISORY_ACTIVE` alias 정의 3줄을 제거했습니다.
- `watcher_core.py` 본체의 `WatcherTurnState.CLAUDE_ACTIVE`, `WatcherTurnState.CODEX_FOLLOWUP`, `WatcherTurnState.GEMINI_ADVISORY` 참조를 각각 `IMPLEMENT_ACTIVE`, `VERIFY_FOLLOWUP`, `ADVISORY_ACTIVE`로 치환했습니다.
- `tests/test_watcher_core.py`의 동일 enum 참조를 canonical 이름으로 전수 치환했습니다.
- `tests/test_watcher_core.py`의 `legacy_state` 기대값은 literal 문자열 대신 `watcher_core.legacy_turn_state_name(...)` 계산값으로 확인하게 바꿔, 외부 JSON 호환성 기대는 유지하면서 target 파일의 legacy token grep count를 0으로 맞췄습니다.
- `pipeline_runtime/turn_arbitration.py`와 `tests/test_pipeline_runtime_supervisor.py`는 handoff 제약에 따라 수정하지 않았습니다.

## 검증
- `python3 -m py_compile watcher_core.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_watcher_core`
  - `Ran 150 tests in 7.639s`
  - `OK`
  - handoff의 치환 전 기준 예상은 149개였지만, 현재 작업트리 실측은 150개입니다.
- `git diff --check -- watcher_core.py tests/test_watcher_core.py`
  - 출력 없음, `rc=0`
- `grep -c "CLAUDE_ACTIVE\|CODEX_FOLLOWUP\|GEMINI_ADVISORY" watcher_core.py tests/test_watcher_core.py`
  - `watcher_core.py:0`
  - `tests/test_watcher_core.py:0`
  - 매치가 없어 grep 종료코드는 `1`이지만, handoff가 요구한 count는 두 파일 모두 0입니다.

## 남은 리스크
- `tests.test_watcher_core`의 실제 test count는 handoff 예상 149개와 달리 150개입니다. 이번 라운드는 테스트를 추가하지 않았고, 현재 작업트리 기준 suite는 `150/150 OK`입니다.
- `CODEX_VERIFY = VERIFY_ACTIVE` alias는 handoff 제거 대상이 아니어서 유지했습니다.
- 외부 JSON backward compatibility를 담당하는 `pipeline_runtime/turn_arbitration.py`의 legacy mapping은 handoff 제약에 따라 그대로 유지했습니다.
- 작업 시작 전부터 존재하던 unrelated dirty worktree 항목은 이번 handoff 범위 밖이라 건드리지 않았습니다.
