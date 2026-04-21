# 2026-04-21 runtime progress phase hints

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `pipeline_gui/home_controller.py`
- `pipeline_gui/home_presenter.py`
- `pipeline-launcher.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `tests/test_pipeline_gui_home_controller.py`
- `tests/test_pipeline_launcher.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 사용 skill
- `security-gate`: runtime status/log 표시 경계가 pane/control 판단에 영향을 주지 않는지 확인했습니다.
- `doc-sync`: 새 `progress.phase` 계약을 runtime 문서에 동기화했습니다.
- `work-log-closeout`: 변경/검증/리스크를 현재 라운드 closeout으로 남겼습니다.

## 변경 이유
- active lane이 실제로는 검증 후 control 정리 중이어도 status/GUI에는 `WORKING + followup`처럼만 보여 사람이 판단하던 "조금 기다리면 되는 상태"가 드러나지 않았습니다.
- pane transcript를 current truth로 삼으면 drift가 커지므로, supervisor가 canonical status 재료만으로 진행 힌트를 계산하는 쪽으로 좁게 보강했습니다.

## 핵심 변경
- supervisor가 `turn_state`, `active_round`, 최신 work/verify mtime, control/autonomy block으로 `status.progress.phase`를 계산합니다.
- active lane에는 같은 phase를 `progress_phase` / `progress_reason`으로 복사합니다.
- phase 예시는 `running_verification`, `verify_note_written_next_control_pending`, `operator_gate_followup`, `next_control_pending`, `receipt_close_pending`입니다.
- GUI agent card와 launcher pane snapshot은 `progress_phase`를 한국어 operator-facing label로 우선 표시하고, 상세 console에는 raw note와 raw phase를 남깁니다.
- runtime docs/QA/runbook에 `progress` block은 current truth가 아니라 operator-facing progress hint이며 pane transcript는 debug 보조라는 경계를 명시했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_gui/home_controller.py pipeline_gui/home_presenter.py pipeline-launcher.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_progress_hint_marks_verify_note_written_next_control_pending tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_progress_hint_marks_operator_gate_followup`
- 통과: `python3 -m unittest tests.test_pipeline_gui_home_presenter.PipelineGuiHomePresenterTest.test_build_agent_card_presentations_localizes_machine_notes tests.test_pipeline_gui_home_controller.PipelineGuiHomeControllerTest.test_build_snapshot_uses_runtime_status_as_single_source`
- 통과: `python3 -m unittest tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_pane_snapshots_include_verify_round_context_for_codex`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor`
- 통과: `python3 -m unittest tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_home_controller tests.test_pipeline_launcher`
- 통과: `git diff --check -- pipeline_runtime/supervisor.py pipeline_gui/home_controller.py pipeline_gui/home_presenter.py pipeline-launcher.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_gui_home_presenter.py tests/test_pipeline_gui_home_controller.py tests/test_pipeline_launcher.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- 실패 후 재실행 통과: `python3 -m unittest tests.test_pipeline_gui_home_presenter.PipelineGuiHomePresenterTest.test_build_agent_card_presentations_localizes_machine_notes tests.test_pipeline_gui_home_controller.PipelineGuiHomeControllerTest.test_build_snapshot_uses_runtime_status_as_single_source tests.test_pipeline_launcher.PipelineLauncherTest.test_pane_snapshots_include_verify_round_context_for_codex`는 잘못된 test class 이름 때문에 실패했고, 올바른 class 이름으로 재실행했습니다.

## 남은 리스크
- 현재 떠 있는 supervisor process는 이번 코드 변경 전 import 상태일 수 있으므로, live UI에 `progress.phase`가 보이려면 다음 runtime start/restart 경계에서 새 supervisor가 로드되어야 합니다.
- 이번 slice는 "애매한 상태를 더 잘 보이게 하는 진행 힌트"까지입니다. phase별 자동 follow-up/timeout 정책은 별도 replay test와 함께 추가해야 합니다.
