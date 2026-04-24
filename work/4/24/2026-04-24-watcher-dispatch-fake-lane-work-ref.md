# 2026-04-24 watcher dispatch fake lane work ref

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `scripts/pipeline_runtime_fake_lane.py`
- `tests/test_pipeline_runtime_fake_lane.py`
- `work/4/24/2026-04-24-watcher-dispatch-fake-lane-work-ref.md`

## 사용 skill
- `work-log-closeout`: pre-existing dirty 변경의 실제 파일, 검증 결과, 남은 리스크를 한국어 `/work` closeout으로 기록했습니다.

## 변경 이유
- `watcher_core.py`: Claude dispatch 직후 프롬프트 echo가 남아도 실제 busy/ready 출력이 나타나면 성공으로 판정해 불필요한 재시도/실패를 줄이기 위해 변경됐습니다.
- `tests/test_watcher_core.py`: prompt echo 이후 busy 출력, 빠른 ready 출력, 활동 없는 prompt 고착 케이스를 구분하는 회귀 테스트가 추가됐습니다.
- `scripts/pipeline_runtime_fake_lane.py`: synthetic verify note가 prompt의 `WORK` 필드를 받아 관련 work ref를 기록하도록 변경됐습니다.
- `tests/test_pipeline_runtime_fake_lane.py`: fake lane verify note에 `WORK` ref가 포함되는 최소 회귀 검증이 추가됐습니다.

## 핵심 변경
- `watcher_core._dispatch_claude()`가 paste 직후 pane snapshot을 저장하고, Enter 후 snapshot 변화가 있으면 shared lane-surface busy marker 또는 idle 판정으로 dispatch 성공을 인정합니다.
- watcher dispatch 판정은 `busy_markers_for_lane("Claude")`와 `text_matches_markers()`를 재사용해 새 문자열 휴리스틱을 만들지 않습니다.
- fake lane verify rendering은 `_render_verify_note(control_seq, route, work_ref)`로 `WORK` ref를 `## 변경 파일`에 반영합니다.
- 이번 라운드 직접 코드 편집은 없습니다. 기존 dirty 4개 파일을 검증하고 closeout만 새로 작성했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py scripts/pipeline_runtime_fake_lane.py tests/test_pipeline_runtime_fake_lane.py`
  - 통과: 출력 없음
- `python3 -m unittest -v tests.test_watcher_core tests.test_pipeline_runtime_fake_lane 2>&1 | tail -5`
  - 통과: `Ran 204 tests in 11.011s`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py scripts/pipeline_runtime_fake_lane.py tests/test_pipeline_runtime_fake_lane.py`
  - 통과: 출력 없음

## 남은 리스크
- 이번 라운드는 handoff 지시에 따라 `make e2e-test`와 broader browser/e2e 검증을 실행하지 않았습니다.
- untracked soak report artifacts(`report/pipeline_runtime/verification/2026-04-24-pipeline-runtime-synthetic-*.json/md`)는 코드 변경이 아니며 이번 closeout 변경 파일에서 제외했습니다.
- commit, push, branch/PR publish, next-slice 선택은 하지 않았습니다.
