# 2026-04-23 GUI automation health presenter

## 변경 파일
- `pipeline_gui/app.py`
- `pipeline_gui/home_presenter.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `work/4/23/2026-04-23-gui-automation-health-presenter.md`

## 사용 skill
- `work-log-closeout`: 기존 GUI dirty 변경의 파일 범위, 검증 결과, 남은 리스크를 한국어 `/work` 노트로 남기기 위해 사용.

## 변경 이유
- `pr_merge_head_mismatch` recovery 이후 canonical control은 `none`으로 내려갔지만, compatibility/debug surface의 `operator_request.md`가 GUI에서 활성 operator wait처럼 보일 수 있었다.
- 이 경우 실제 상태는 operator 대기가 아니라 verify/recovery 후속 처리이므로, GUI가 `automation_health`를 함께 보고 verify activity를 우선 표시해야 한다.
- 반대로 runtime이 실제 `automation_health=needs_operator`를 보고하면 기존처럼 operator wait red 상태를 유지해야 한다.

## 핵심 변경
- `pipeline_gui/app.py`는 runtime snapshot의 `automation_health` 값을 `build_control_presentation()`에 전달한다.
- `pipeline_gui/home_presenter.py`는 `verify_activity`가 있고 `automation_health != "needs_operator"`이면 compatibility operator slot보다 verify/recovery 표시를 우선한다.
- `automation_health="needs_operator"`일 때는 실제 operator wait를 red palette로 유지해 operator boundary를 숨기지 않는다.
- `tests/test_pipeline_gui_home_presenter.py`는 recovery verify activity가 compatibility operator slot보다 우선되는 사례와 실제 operator wait가 red로 남는 사례를 추가로 검증한다.
- 이번 라운드는 위 세 파일의 기존 dirty 변경을 문서화한 closeout이며, 코드 파일 자체는 수정하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` → 요청된 handoff SHA `a21c42702f74e1206b3117196554ff658b4d1cae119bcfe4eecf22314fe9d364`와 일치.
- `python3 -m py_compile pipeline_gui/app.py pipeline_gui/home_presenter.py tests/test_pipeline_gui_home_presenter.py` → 통과.
- `python3 -m unittest tests.test_pipeline_gui_home_presenter -v` → 20개 테스트 통과.
- `git diff -- pipeline_gui/app.py pipeline_gui/home_presenter.py tests/test_pipeline_gui_home_presenter.py` → diff 확인 완료.
- `git diff --check -- pipeline_gui/app.py pipeline_gui/home_presenter.py tests/test_pipeline_gui_home_presenter.py` → 통과.

## 남은 리스크
- Tk GUI를 실제 화면으로 실행해 시각 확인하지는 않았다. 이번 handoff acceptance가 presenter unit test와 compile/whitespace 확인에 한정되어 생략했다.
- 이 노트는 pre-existing dirty GUI 변경의 감사 추적 보강이다. verify owner가 커밋 범위를 잡을 때 기존 `verify/` 변경과 다른 dirty 파일 여부를 별도로 확인해야 한다.
