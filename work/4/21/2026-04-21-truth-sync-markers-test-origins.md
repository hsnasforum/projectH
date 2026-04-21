# 2026-04-21 truth-sync markers test origins

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/4/21/2026-04-21-truth-sync-markers-test-origins.md` (새 파일)

## 사용 skill
- `security-gate`: operator stop 후보 분류 marker가 runtime control routing에 영향을 주는 변경이므로, 새 삭제/덮어쓰기/외부 네트워크/commit/push/PR 동작을 만들지 않는지 확인했습니다.
- `finalize-lite`: 구현 종료 전 실행한 검증, docs sync 불필요 여부, `/work` closeout 준비 상태를 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 실패 후 보정 이력, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 635 지시에 따라 seq 631 `/work`가 주장했지만 실제 코드에 없던 git/milestone blocker marker를 `_MENU_CHOICE_BLOCKER_MARKERS`에 맞췄습니다.
- supervisor/watcher suite에 남은 출처 미기록 테스트에 origin 주석을 남겨, dirty worktree의 테스트 baseline 증가 원인을 추적 가능하게 했습니다.

## 핵심 변경
- `_MENU_CHOICE_BLOCKER_MARKERS` 튜플 끝에 지정된 5개 marker만 추가했습니다: `커밋`, `commit`, `push`, `milestone`, `마일스톤`.
- `tests/test_operator_request_schema.py`에 `test_menu_choice_blocker_markers_includes_git_markers`를 추가해 위 5개 marker 존재를 고정했습니다.
- `tests/test_pipeline_runtime_supervisor.py`의 출처 미기록 테스트 4개에 origin 주석을 추가했습니다.
  - `test_classify_operator_candidate_defaults_decision_class_per_visible_mode`: `# origin: seq 593 dispatch_intent/lane-identity default decision-class guard (출처 work note 미기록)`
  - `test_classify_operator_candidate_inline_parenthesized_choices_route_to_advisory_followup`: `# origin: choice-menu inline parenthesized advisory follow-up guard (출처 work note 미기록)`
  - `test_classify_operator_candidate_body_marker_docs_do_not_block_choice_menu`: `# origin: choice-menu explanatory blocker marker scope guard (출처 work note 미기록)`
  - `test_classify_operator_candidate_payload_stability`: `# origin: seq 593 dispatch_intent/lane-identity payload stability guard (출처 work note 미기록)`
- `tests/test_watcher_core.py`의 출처 미기록 테스트 1개에 origin 주석을 추가했습니다.
  - `test_deferred_handoff_releases_after_implement_lane_becomes_idle`: `# origin: implement handoff idle-release deferred-candidate replay (출처 work note 미기록)`
- 새 blocker marker가 들어오면서 기존 watcher choice-menu fixture 4개가 `commit`/`push`/`milestone` 단어 때문에 operator blocker로 분류되어 실패했습니다. 분류기 로직은 변경하지 않고, agent-resolvable choice-menu fixture의 결정 문구만 `docs and verify notes`, `evidence follow-up`, `docs reconciliation`처럼 blocker-free 문구로 보정했습니다.

## 검증
- Codex implement 세션 재검증:
  - `python3 -m py_compile pipeline_runtime/operator_autonomy.py`
    - 출력 없음, `rc=0`
  - `python3 -m unittest tests.test_operator_request_schema`
    - `Ran 9 tests in 0.001s`
    - `OK`
  - `python3 -m unittest tests.test_pipeline_runtime_supervisor`
    - `Ran 117 tests in 0.742s`
    - `OK`
  - `python3 -m unittest tests.test_watcher_core`
    - `Ran 159 tests in 7.820s`
    - `OK`
  - `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
    - 출력 없음, `rc=0`
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_operator_request_schema`
  - `Ran 9 tests in 0.001s`
  - `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 117 tests in 0.782s`
  - `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 첫 실행: `Ran 159 tests in 7.599s`, `FAILED (failures=4)`
  - 실패 원인: 새 `commit`/`push`/`milestone` marker가 기존 choice-menu fixture의 결정 문구와 충돌했습니다.
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest.test_choice_menu_operator_request_routes_to_followup tests.test_watcher_core.TurnResolutionTest.test_numbered_choice_menu_operator_request_routes_to_followup tests.test_watcher_core.TurnResolutionTest.test_parenthesized_inline_choice_operator_request_routes_to_followup tests.test_watcher_core.TurnResolutionTest.test_choice_menu_operator_request_ignores_explanatory_body_blocker_markers`
  - `Ran 4 tests in 0.036s`
  - `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - fixture 보정 후 재실행: `Ran 9 tests in 0.001s`, `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - fixture 보정 후 재실행: 출력 없음, `rc=0`
- `python3 -m unittest tests.test_watcher_core`
  - 최종 재실행: `Ran 159 tests in 7.749s`
  - `OK`

## 남은 리스크
- live restart 재검증은 이번 implement lane 범위가 아니어서 수행하지 않았습니다. handoff 기준 Claude verify 담당으로 남아 있습니다.
- branch commit/push/PR은 진행하지 않았습니다. operator 결정은 여전히 대기입니다.
- 이번 변경은 marker tuple, marker 존재 회귀 테스트, 기존 테스트 출처 주석, choice-menu fixture 문구 보정에 한정했습니다. `pipeline_runtime/supervisor.py`, `.pipeline/gemini_request.md`, `.pipeline/operator_request.md`는 수정하지 않았습니다.
