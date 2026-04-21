# 2026-04-21 stale advisory presentation surface

## 변경 파일
- `pipeline-launcher.py`
- `pipeline_gui/home_presenter.py`
- `pipeline_runtime/status_labels.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `work/4/21/2026-04-21-stale-advisory-presentation-surface.md`

## 사용 skill
- `finalize-lite`: 표시 변경 범위, 실행한 검증, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 명령만 기준으로 이 closeout을 남겼습니다.

## 변경 이유
- seq 698에서 `stale_advisory_pending`이 automation health snapshot에 추가됐지만, launcher line-mode와 GUI console detail에는 아직 표시되지 않았습니다.
- 이번 slice는 watcher/supervisor 로직을 바꾸지 않고, 이미 canonical status에 있는 field를 operator가 볼 수 있게 하는 presentation-only 보강입니다.

## 핵심 변경
- `pipeline_runtime/status_labels.py`에 `stale_advisory_pending` 표시 라벨 `어드바이저리 요청 대기 중`을 추가했습니다.
- `pipeline-launcher.py`가 runtime status의 `stale_advisory_pending`을 `runtime_view`에 전달하고, line-mode `Automation detail`에 한국어 라벨과 `stale_advisory_pending=true`를 함께 표시하도록 했습니다.
- `pipeline_gui/home_presenter.py`가 snapshot의 `stale_advisory_pending`을 console detail에 표시하도록 했습니다.
- launcher와 GUI presenter 각각에 stale advisory pending 표시 테스트를 추가했습니다.
- `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/operator_request.md`는 수정하지 않았고, watcher/supervisor 로직도 건드리지 않았습니다.

## 검증
- `python3 -m py_compile pipeline-launcher.py pipeline_gui/home_presenter.py pipeline_runtime/status_labels.py` → 통과
- `python3 -m unittest tests.test_pipeline_launcher tests.test_pipeline_gui_home_presenter` → 45 tests OK
- `git diff --check pipeline-launcher.py pipeline_gui/home_presenter.py pipeline_runtime/status_labels.py tests/test_pipeline_launcher.py tests/test_pipeline_gui_home_presenter.py` → 통과
- `sha256sum .pipeline/claude_handoff.md` → `e8cc8ca8ccfa19741d05ac09789108c7a91ec85633681dad4088b9aa20bb13cf` 유지 확인

## 남은 리스크
- 이번 round는 handoff 지정 범위에 맞춰 launcher line-mode와 GUI presenter 표시만 다뤘습니다. browser/E2E GUI 실행 검증은 수행하지 않았습니다.
- worktree에는 이전 seq 691/697/698 계열 dirty 변경이 함께 남아 있습니다. 이번 round는 해당 변경을 되돌리거나 commit/push하지 않았습니다.
