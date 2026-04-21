# 2026-04-21 blocker markers sequential gate fix

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/21/2026-04-21-blockermarkers-sequential-gate-fix.md` (새 파일)

## 사용 skill
- `security-gate`: operator stop 후보 분류와 runtime control routing에 영향을 주는 변경이 approval/save, 삭제/덮어쓰기, 외부 네트워크, 사용자 파일 쓰기를 새로 만들지 않는지 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 실측 결과, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 631 지시에 따라 `_MENU_CHOICE_BLOCKER_MARKERS`가 B/C/D 순차 승인 게이트를 병렬 선택지로 오감지하지 않도록 blocker marker를 보강했습니다.
- `suppress_until: 2026-04-22` 전에 false-positive 원인을 좁게 막는 것이 목적이며, supervisor event aggregation이나 branch commit/PR 흐름은 이번 범위에서 제외했습니다.

## 핵심 변경
- `_MENU_CHOICE_BLOCKER_MARKERS`에 순차 게이트 지시어 `통과 후`, `완료 후`를 추가했습니다. `이후`는 handoff 지시대로 너무 광범위할 수 있어 추가하지 않았습니다.
- git/milestone 동작 계열 blocker로 `커밋`, `commit`, `push`, `푸시`, `milestone`, `마일스톤`, `브랜치`, `pr approval`, `pr 승인`을 추가했습니다. bare `pr`는 `proposal` 같은 일반 단어를 오탐할 수 있어 승인/approval 문맥으로만 제한했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 `test_classify_operator_candidate_sequential_gate_not_misrouted`를 추가해 `(B)`, `(C) B 통과 후 ...`, `(D) C 완료 후 ...` 형태가 `slice_ambiguity` / `next_slice_selection`으로 바뀌지 않도록 고정했습니다.
- 기존 choice-menu 회귀 fixture 중 agent-resolvable 선택지로 남아야 하는 케이스는 새 blocker 단어와 섞이지 않도록 `decision_required` 문구를 조정했습니다.
- 분류기 로직은 수정하지 않았고, marker tuple과 테스트만 변경했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 116 tests in 0.722s`
  - `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - `Ran 8 tests in 0.001s`
  - `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 출력 없음, `rc=0`

## 남은 리스크
- supervisor event aggregation의 AXIS-G4 e2e gap은 이번 slice에서 수정하지 않았습니다. Gemini seq 630 기준 C 슬라이스로 남아 있으며 다음 라운드 대상입니다.
- branch commit/push/PR은 이번 implement lane에서 진행하지 않았습니다. operator 결정 C 및 aggregation 완료 후 별도 승인 대상입니다.
- `tests.test_pipeline_runtime_supervisor`는 기존 작업 트리의 추가 supervisor 회귀 테스트까지 포함해 현재 116개가 실행됐습니다. handoff의 예상 수치인 112개와 다르지만, 이번 실행 결과는 전체 suite green입니다.
- 이번 변경은 local classifier marker/test 변경만 포함합니다. approval/save flow, 삭제/덮어쓰기, 외부 네트워크, production runtime restart, commit/push/PR은 수행하지 않았습니다.
