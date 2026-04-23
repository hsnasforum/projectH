# 2026-04-23 test isolation fix

## 변경 파일
- `tests/test_web_app.py`
- `work/4/23/2026-04-23-test-isolation-fix.md`

## 사용 skill
- `finalize-lite`: handoff acceptance 검증과 변경 범위가 테스트 fixture에만 머무는지 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 결과를 `/work` 형식에 맞춰 기록했습니다.

## 변경 이유
- 직전 M15 Axis 1 추가 확인에서 `test_submit_candidate_review_accept_persists_local_preference_candidate`가 `corrections_dir` 기본값 `data/corrections`를 사용해 repo-local correction evidence를 읽는 fixture 격리 문제가 드러났습니다.
- 이 실패는 production 변경 regression이 아니라 기존 테스트가 temp correction store를 지정하지 않은 문제였습니다.
- handoff는 해당 단일 테스트의 `AppSettings` 호출만 격리하도록 요청했습니다.

## 핵심 변경
- `test_submit_candidate_review_accept_persists_local_preference_candidate`의 `AppSettings(...)`에 `artifacts_dir=str(tmp_path / "artifacts")`를 추가했습니다.
- 같은 `AppSettings(...)`에 `corrections_dir=str(tmp_path / "corrections")`를 추가해 real `data/corrections`를 읽지 않도록 했습니다.
- production code, 다른 테스트, `.pipeline` control slot은 변경하지 않았습니다.

## 검증
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate -v`
  - 통과: `1 test`
- `git diff --check -- tests/test_web_app.py`
  - 통과: 출력 없음

## 남은 리스크
- 전체 `tests.test_web_app`와 전체 test suite는 실행하지 않았습니다.
- 동일한 fixture isolation gap이 다른 테스트에도 있을 수 있지만, 이번 handoff boundary에 따라 현재 실패한 단일 테스트만 수정했습니다.
