# 2026-04-22 eval family trace TypedDicts

## 변경 파일
- `core/eval_contracts.py`
- `eval/__init__.py`
- `work/4/22/2026-04-22-eval-family-trace-typeddicts.md`

## 사용 skill
- `finalize-lite`: 구현 종료 전 실행한 체크, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 853이 Milestone 8 Axis 4의 지연 항목인 family-specific trace extension 필드 정의를 요구했습니다.
- 이번 구현 범위는 `EvalFixtureFamily` 7개 family 각각에 대응하는 `TypedDict` 정의와 export 추가로 제한되었습니다.

## 핵심 변경
- `EvalArtifactCoreTrace`를 상속하는 family별 `TypedDict` 7개를 `total=False`로 추가했습니다.
- 각 family trace는 handoff에 지정된 추가 필드 2개 이하만 포함했습니다.
- `EVAL_FAMILY_TRACE_CLASS`에 `EvalFixtureFamily` 값별 trace class 매핑을 추가했습니다.
- `eval/__init__.py`에서 새 trace `TypedDict` 7개와 `EVAL_FAMILY_TRACE_CLASS`를 export했습니다.
- handoff 제약에 따라 `eval/fixture_loader.py`, `data/eval/fixtures/`, 테스트 파일, 문서 파일은 수정하지 않았습니다.

## 검증
- `python3 -m py_compile core/eval_contracts.py eval/__init__.py` -> 통과
- `python3 -m unittest tests.test_eval_loader -v` -> 7개 테스트 통과
- `git diff --check -- core/eval_contracts.py eval/__init__.py` -> 통과

## 남은 리스크
- 이번 라운드는 타입 계약과 export만 추가했으며 fixture validation 로직이나 JSON fixture enrichment는 handoff 범위 밖이라 변경하지 않았습니다.
- 문서 동기화는 handoff에서 금지되어 수행하지 않았습니다. 필요하면 별도 verify/handoff 라운드에서 판단해야 합니다.
