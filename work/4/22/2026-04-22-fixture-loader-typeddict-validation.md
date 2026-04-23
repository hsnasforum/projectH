# 2026-04-22 fixture loader TypedDict validation

## 변경 파일
- `eval/fixture_loader.py`
- `tests/test_eval_loader.py`
- `work/4/22/2026-04-22-fixture-loader-typeddict-validation.md`

## 사용 skill
- `finalize-lite`: 필수 체크 통과 여부, 문서 동기화 범위, `/work` closeout 준비 상태를 구현 종료 전에 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 862가 `EVAL_FAMILY_TRACE_CLASS` 기반 family-specific field validation을 `eval/fixture_loader.py`에 연결하도록 지시했습니다.
- seq 853의 family-specific `TypedDict` 정의와 seq 858의 fixture enrichment 사이에 loader validation이 unknown key와 type mismatch를 적극 거절하지 않는 간극이 있었습니다.

## 핵심 변경
- `_validate()`가 fixture family별 trace class를 찾아 family-specific 필드 목록을 계산하도록 했습니다.
- core trace 필드는 기존 required field 검증에 맡기고, family-specific optional field만 타입 검증 대상으로 분리했습니다.
- family별 허용 필드 밖의 추가 키가 들어오면 `ValueError`를 발생시키도록 했습니다.
- family-specific 필드가 있을 때 값 타입이 `TypedDict` annotation과 맞지 않으면 `ValueError`를 발생시키도록 했습니다.
- `tests/test_eval_loader.py`에 unknown family field와 field type mismatch reject 테스트 2개를 추가했습니다.

## 검증
- `python3 -m py_compile eval/fixture_loader.py tests/test_eval_loader.py` -> 통과
- `python3 -m unittest tests.test_eval_loader -v` -> 9개 테스트 통과
- `git diff --check -- eval/fixture_loader.py tests/test_eval_loader.py` -> 통과

## 남은 리스크
- 이번 라운드는 loader validation과 단위 테스트만 변경했습니다.
- handoff 제약에 따라 `core/eval_contracts.py`, `eval/__init__.py`, fixture JSON, docs 파일은 수정하지 않았습니다.
