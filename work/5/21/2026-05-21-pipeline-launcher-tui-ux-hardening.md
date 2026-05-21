# 2026-05-21 Pipeline launcher TUI UX hardening

## 변경 파일

- `pipeline-launcher.py`
- `tests/test_pipeline_launcher.py`
- `work/5/21/2026-05-21-pipeline-launcher-tui-ux-hardening.md`

## 사용 skill

- `security-gate`: launcher의 runtime stop/restart 호출, subprocess timeout 방어, curses TUI 상태 표시가 runtime control 경계에 닿으므로 로컬 실행/표시 경계가 넓어지지 않는지 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실패 확인, 검증 결과, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `report/gemini/2026-05-21-launcher-analysis.md`와 `.pipeline/advisory_advice.md`에서 TUI launcher 쪽 운영 안정성 이슈가 확인되었습니다.
- 기존 runtime 로직 수정과 별개로, 사용자 접점인 `pipeline-launcher.py`가 stop 중 UI freeze, CJK 폭 계산 오류, resize 미대응, timeout crash에 취약했습니다.

## 핵심 변경

- TUI stop/restart를 `BackgroundAction` 기반 background thread로 분리했습니다. `T` 키 stop 중에는 `STOP: 중지 중...`을 표시하면서 curses 루프가 계속 키 입력을 받습니다.
- `unicodedata.east_asian_width()` 기반 `_display_width`, `_clip_display_width`, `_fit_text`, `_tail_display_width`를 추가하고 `safe_addstr()`와 주요 렌더링 slice가 CJK 폭 기준으로 자르도록 바꿨습니다.
- `curses.KEY_RESIZE` 이벤트를 처리하는 `handle_resize()`를 추가해 `curses.update_lines_cols()`와 `clearok(True)` 후 즉시 redraw하도록 했습니다.
- `_run_runtime_cli()`가 `subprocess.TimeoutExpired`, `subprocess.SubprocessError`, `OSError`를 `CompletedProcess` 실패 결과로 변환하게 해 launcher crash 대신 UI 메시지로 흐르게 했습니다.
- timeout, background stop, CJK width/clipping, resize handler 회귀 테스트를 추가했습니다.

## 검증

- 수정 전 실패 확인:
  - `python3 -m unittest -v tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_run_runtime_cli_timeout_returns_failed_completed_process tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_background_stop_action_returns_before_pipeline_stop_finishes tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_fit_text_uses_cjk_display_width tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_safe_addstr_clips_by_cjk_display_width tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_handle_resize_marks_screen_for_redraw`
  - 결과: timeout 예외가 그대로 올라왔고, background stop helper와 CJK width/resize helper가 없었으며, `safe_addstr()`가 `한글abc`를 폭 4에서 `한글ab`로 잘못 잘랐습니다.
- 수정 후 focused 확인:
  - 같은 5개 테스트
  - `Ran 5 tests in 0.014s` / `OK`.
- 컴파일 확인:
  - `python3 -m py_compile pipeline-launcher.py`
  - 통과했습니다.
- 전체 launcher 테스트 확인:
  - `python3 -m unittest tests.test_pipeline_launcher -v`
  - `Ran 37 tests in 0.064s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline-launcher.py tests/test_pipeline_launcher.py work/5/21`
  - closeout 작성 전후 모두 통과했습니다.

## 남은 리스크

- 실제 curses 화면에서 수동 리사이즈와 stop 중 키 입력을 live runtime으로 직접 검증하지는 않았습니다.
- Playwright, E2E, live runtime start/stop 검증은 요청 범위 밖이라 실행하지 않았습니다.
- Gemini 보고서의 L5~L10 전체를 처리한 것은 아니며, 이번 라운드는 사용자가 지정한 non-blocking stop, CJK 폭 계산, resize, timeout crash 방어에 한정했습니다.
- commit, push, PR publish, merge, release는 수행하지 않았습니다.
