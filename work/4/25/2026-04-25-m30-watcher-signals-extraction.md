# 2026-04-25 M30 watcher signals extraction

## 변경 파일
- `watcher_core.py`
- `watcher_signals.py`
- `tests/test_watcher_signals.py`
- `work/4/25/2026-04-25-m30-watcher-signals-extraction.md`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- `CONTROL_SEQ: 144` implement handoff에 따라 `watcher_core.py`에 남아 있던 live-session escalation, implement blocked, forbidden menu, completed-handoff 신호 추출 순수 함수와 regex 상수를 별도 모듈로 분리해야 했습니다.
- `watcher_core.py`의 기존 `_extract_*` mock/import 계약은 유지하면서, 신호 파싱 로직을 직접 단위 테스트할 수 있는 작은 모듈 경계를 만들기 위한 작업입니다.

## 핵심 변경
- `watcher_signals.py`를 추가하고 live-session escalation, implement blocked, forbidden menu, completed-handoff 신호 추출 함수와 관련 regex/상수, `_HandoffSentenceReplacementTarget`을 옮겼습니다.
- `watcher_core.py`의 기존 신호 추출 블록을 `watcher_signals` import 블록으로 교체해 기존 `watcher_core._extract_*` 이름 바인딩을 유지했습니다.
- `watcher_core.py`의 보존 대상 함수 `_line_looks_like_input_prompt`, `_pane_text_has_gemini_ready_prompt`, `_pane_has_input_cursor`, `_pane_has_working_indicator`는 수정하지 않았습니다.
- `watcher_signals.py`는 순수 파싱 모듈로 유지하고 `WatcherCore`, timer, thread 의존 코드는 추가하지 않았습니다.
- `tests/test_watcher_signals.py`를 추가해 기존 `tests/test_watcher_core.py`의 10개 신호 추출 테스트를 `watcher_signals` 직접 import 버전으로 복사했습니다. 기존 `tests/test_watcher_core.py` 테스트는 이번 slice에서 수정하지 않았습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `196ca1c7d99d462ff86454fb554cecbc804fbe0ec71a88a4799236a45c8a7824`
- `python3 -m py_compile watcher_core.py watcher_signals.py`
  - 통과: 출력 없음
- `python3 -m py_compile watcher_core.py watcher_signals.py tests/test_watcher_signals.py`
  - 통과: 출력 없음
- `python3 -m unittest tests/test_watcher_core.py -v 2>&1 | tail -5`
  - 통과: `Ran 202 tests`, `OK`
- `python3 -m unittest tests/test_watcher_signals.py -v 2>&1 | tail -5`
  - 통과: `Ran 10 tests`, `OK`
- `grep -n "^def _extract_implement_blocked_signal\|^def _extract_live_session\|^def _normalize_escalation\|^def _decode_handoff\|^def _parse_handoff\|^def _normalize_control_path" watcher_core.py`
  - 통과: 매치 없음, exit code 1
- `git diff --check -- watcher_core.py watcher_signals.py tests/test_watcher_signals.py`
  - 통과: 출력 없음
- `git diff --check -- watcher_core.py watcher_signals.py tests/test_watcher_signals.py work/4/25`
  - 통과: 출력 없음

## 남은 리스크
- 이번 slice는 watcher 신호 파싱 모듈 분리에 한정했습니다. browser/E2E, 전체 unittest, pipeline live soak는 실행하지 않았습니다.
- 작업 시작 전 repo에는 다른 파일의 dirty state가 이미 많았습니다. 특히 `tests/test_watcher_core.py`는 직전 Axis 2 작업의 dirty 변경이 남아 있었고, 이번 Axis 3에서는 기존 테스트 로직이나 mock target을 추가로 수정하지 않았습니다.
- `watcher_signals.py` 안에는 `watcher_core.py`의 보존 함수와 동일한 prompt-line 판별 helper가 독립적으로 들어 있습니다. 이는 새 모듈이 `watcher_core`를 역참조하지 않도록 하기 위한 좁은 중복이며, 추후 lane-surface 또는 공용 parsing helper로 모을 수 있습니다.
