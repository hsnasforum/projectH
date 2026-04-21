# 2026-04-21 supervisor test baseline truth-sync role confidence

## 변경 파일
- `core/agent_loop.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/21/2026-04-21-supervisor-test-baseline-truth-sync-role-confidence.md`

## 사용 skill
- `work-log-closeout`: handoff 수행 후 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 closeout 형식으로 정리했습니다.

## 변경 이유
- AXIS-G13: supervisor regression suite의 현재 기준이 `106/106 OK`임을 코드 주석으로 정식화하고, seq 593 `dispatch_intent`/lane-identity 라운드에서 문서화 없이 추가된 두 테스트의 출처를 남겼습니다.
- AXIS-G10: `role_confidence`가 `SourceRole.COMMUNITY`를 `.get(..., 0.4)` fallback으로만 처리하던 상태를 명시 키로 고정해, fallback 값 변경 시 COMMUNITY confidence가 조용히 바뀌는 회귀를 줄였습니다.

## 핵심 변경
- `test_classify_operator_candidate_defaults_decision_class_per_visible_mode` 바로 위에 seq 593 origin 주석 1줄을 추가했습니다.
- `test_classify_operator_candidate_payload_stability` 바로 위에 동일한 seq 593 origin 주석 1줄을 추가했습니다.
- `core/agent_loop.py`의 entity source `role_confidence` dict에 `SourceRole.COMMUNITY: 0.4,`를 추가했습니다.
- 테스트 로직, test count, runtime classification 동작은 변경하지 않았습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 106 tests in 0.670s`
  - `OK`
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py core/agent_loop.py`
  - 출력 없음, `rc=0`

## 남은 리스크
- supervisor test baseline 주석은 두 테스트의 출처를 정식화하지만, seq 593 당시의 scope violation 자체를 추가로 조사하지는 않았습니다.
- `SourceRole.COMMUNITY` confidence는 기존 fallback과 같은 `0.4`로 명시했으므로 현재 동작 변화는 없고, 향후 fallback 변경에 대한 회귀 방지 성격입니다.
- 작업 시작 전부터 존재하던 unrelated dirty worktree 항목은 이번 handoff 범위 밖이라 건드리지 않았습니다.
