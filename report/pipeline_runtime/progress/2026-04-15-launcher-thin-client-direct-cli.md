# 2026-04-15 launcher thin client direct CLI

## 요약
- `pipeline-launcher.py`의 start/stop/attach 경로를 backend shell wrapper가 아니라 `python3 -m pipeline_runtime.cli` 직접 호출로 정리했습니다.
- launcher의 focused pane raw output viewer를 제거하고, lane status + recent runtime events만 보여주는 runtime detail viewer로 축소했습니다.
- launcher 파일 안에 남아 있던 raw pane reflow / decorative filtering / direct pane capture 보조 코드를 함께 정리했습니다.

## 변경 파일
- `pipeline-launcher.py`
- `tests/test_pipeline_launcher.py`

## 핵심 변경
- launcher는 이제 runtime 상태 surface를 읽고 command client 역할만 수행합니다.
- `start`
  - `pipeline_runtime.cli start ... --no-attach`를 detached subprocess로 실행합니다.
- `stop`
  - `pipeline_runtime.cli stop ...`를 blocking 호출로 실행합니다.
- `attach`
  - launcher 내부 tmux adapter 호출 대신 runtime CLI attach를 직접 실행합니다.
- focused lane view
  - raw pane text 대신 `status.json` lane block과 `events.jsonl` 기반 lane event 요약만 표시합니다.

## 기대 효과
- launcher가 raw pane 관측 권한 없이도 운영용 status viewer + command client로 동작합니다.
- tmux/debug substrate 의존이 launcher 화면 경로에서 더 줄어듭니다.
- pane UI 문자열 변화가 launcher UI를 흔드는 경로를 하나 더 제거했습니다.
