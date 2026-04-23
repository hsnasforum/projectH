# 2026-04-23 PR number parser gate scope

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `work/4/23/2026-04-23-pr-number-parser-gate-scope.md`

## 사용 skill
- `security-gate`: PR merge gate의 operator/publication boundary가 parser 수정으로 우회되지 않는지 점검.
- `finalize-lite`: 구현 종료 전 검증 사실, doc-sync 필요 여부, closeout 준비 상태를 정리.
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 검증, 남은 리스크를 `/work`에 기록.

## 변경 이유
- 이전 `pr_merge_gate` control에서 실제 gate PR은 PR #28이었지만, 설명문에 남은 과거 `PR #27` 언급까지 `referenced_operator_pr_numbers()`가 함께 수집했다.
- 그 결과 이미 merge된 과거 PR의 head가 현재 gate HEAD와 다르다는 이유로 `pr_merge_head_mismatch` 루프가 발생할 수 있었다.
- 현재 gate PR을 명시한 structured/labeled field가 있으면 그 값을 우선해야 하며, 배경 설명의 과거 PR 언급은 gate 판정에 섞이면 안 된다.

## 핵심 변경
- `pipeline_runtime/operator_autonomy.py`에 현재 gate PR 전용 field 목록을 추가했다: `PR`, `PR_URL`, `PULL_REQUEST`, `CURRENT_PR`, `GATE_PR`, `MERGE_PR` 및 number/url 변형.
- 현재 PR field 값에서 `/pull/<n>`, `PR #<n>`, `#<n>`, bare number를 추출하도록 별도 helper를 추가했다.
- `referenced_operator_pr_numbers()`가 structured metadata와 labeled current PR line을 먼저 확인하고, 값이 있으면 그 번호만 반환하도록 바꿨다.
- current PR field가 없을 때는 기존 full-body fallback을 유지해 legacy `PR #27 merge approval` 형식은 계속 동작한다.
- `tests/test_operator_request_schema.py`에 active `PR: https://.../pull/28` line과 과거 `PR #27` 설명문이 함께 있는 회귀 테스트를 추가했다.
- structured metadata의 `pr_url`이 과거 PR 설명문보다 우선되는 회귀 테스트도 추가했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` → 요청된 handoff SHA `c80525634908f39a982ff21d3faacaef0b05818e31735592653c0a9912cb8900`와 일치.
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/pr_merge_state.py` → 통과.
- `python3 -m unittest tests.test_operator_request_schema tests.test_pr_merge_state -v` → 24개 테스트 통과.
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py` → 통과.

## 남은 리스크
- current PR field가 없는 완전 legacy control에서는 기존 fallback이 여전히 전체 본문을 스캔한다. 이는 이번 handoff의 "structured/labeled field가 없을 때만 fallback" 요구에 맞춘 의도된 호환성이다.
- live runtime restart나 Playwright는 실행하지 않았다. 변경 범위가 browser-visible contract가 아닌 parser helper와 focused unit test에 한정되어 생략했다.
- 기존 dirty GUI 파일(`pipeline_gui/app.py`, `pipeline_gui/home_presenter.py`, `tests/test_pipeline_gui_home_presenter.py`)과 기존 `verify/`, `report/gemini/` 변경은 이번 slice 범위 밖이라 건드리지 않았다.
