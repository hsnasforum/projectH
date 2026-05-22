# 2026-05-22 watcher control signals extraction

## 변경 파일
- `watcher_control_signals.py`
- `watcher_core.py`
- `tests/test_watcher_control_signals.py`
- `work/5/22/2026-05-22-watcher-control-signals-extraction.md`

## 사용 skill
- `security-gate`: control slot, advisory/operator stop 신호 판독 경계를 유지하는지 확인하기 위해 사용했습니다.
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `watcher_core.py`에 제어 신호 snapshot 파싱, slot matching, newest signal 선택 로직이 WatcherCore 본문과 함께 남아 있었습니다.
- A3 Step 2 범위는 WatcherCore의 기존 메서드 시그니처를 유지하면서, 순수 로직과 의존성 주입 판독기를 `watcher_control_signals.py`로 분리하는 것이었습니다.

## 핵심 변경
- `watcher_control_signals.py`를 추가해 `ControlSignalReader`, `newest_control_signal()`, `control_signal_matches()`, `control_signal_for_slot()`을 분리했습니다.
- `ControlSignalReader`는 `pipeline_dir`, `advisory_enabled`, `operator_stop_enabled`, `path_sig_fn`을 주입받아 기존 `read_pipeline_control_snapshot()` 기반 판독을 유지합니다.
- `watcher_core.py`는 `self._csreader`를 초기화하고, 기존 `_control_signal_*` 메서드들을 새 reader와 순수 함수 위임으로 교체했습니다.
- WatcherCore의 `_get_path_sig` 캐시 로직은 유지하고 `path_sig_fn=self._get_path_sig`로 주입했습니다.
- `tests/test_watcher_control_signals.py`를 추가해 advisory/operator disabled filtering, advisory advice exclusion, legacy alias matching, 기본 path signature를 검증했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_control_signals.py tests/test_watcher_control_signals.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_watcher_control_signals -v`
  - 결과: `Ran 4 tests in 0.013s`, `OK`.
- 통과: `python3 -m unittest tests.test_watcher_core -v 2>&1 | tail -5`
  - 결과: `Ran 264 tests in 10.771s`, `OK`.
- 통과: `python3 -c "from watcher_control_signals import (ControlSignalReader, newest_control_signal, control_signal_matches, control_signal_for_slot); print('import OK')"`
  - 결과: `import OK`.
- 통과: `git diff --check -- watcher_core.py watcher_control_signals.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 slice는 제어 신호 판독 로직의 위치를 바꾸는 내부 리팩터링입니다. live watcher/tmux runtime 검증은 실행하지 않았습니다.
- `watcher_core.py`는 이전 slice의 helper extraction 변경이 이미 남아 있는 dirty 파일입니다. 이번 slice에서는 제어 신호 reader 초기화와 위임부만 추가로 변경했습니다.
- product docs, agent/skill config, `.pipeline` control slot은 변경하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
