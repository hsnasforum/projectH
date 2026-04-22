# 2026-04-22 candidate review suggested scope enum

## 변경 파일
- `core/contracts.py`
- `storage/session_store.py`
- `work/4/22/2026-04-22-candidate-review-suggested-scope-enum.md`

## 사용 skill
- `security-gate`: session record의 optional `suggested_scope` 저장 검증을 추가하므로 저장/감사 경계를 확인했다.
- `finalize-lite`: handoff 필수 검증, 변경 범위, `/work` closeout 준비 상태를 확인했다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 849
  (`candidate_review_suggested_scope_enum`)에 따라 `candidate_review_record.suggested_scope`
  값 제약을 추가했다.
- Milestone 7 Axis 4에서 deferred였던 "scope value constraints"를
  `message_only`, `family_scoped`, `global_preference` 세 값으로 현재 storage normalize 경로에
  고정했다.

## 핵심 변경
- `core/contracts.py`에 `CandidateReviewSuggestedScope` `StrEnum`을 추가했다.
- `storage/session_store.py`에서 `CandidateReviewSuggestedScope`를 import하고,
  non-empty `suggested_scope`가 들어온 경우 `CandidateReviewSuggestedScope(suggested_scope)`로
  enum member 여부를 검증하도록 했다.
- invalid value는 `ValueError("invalid suggested_scope: ...")`로 거부한다.
- absent, `None`, empty 또는 whitespace-only `suggested_scope`는 기존처럼 optional field로
  남아 저장되지 않는다.
- handoff 제한에 따라 `core/eval_contracts.py`, fixture JSON, tests, docs, `.pipeline` control
  파일은 수정하지 않았다.

## 검증
- `python3 -m py_compile core/contracts.py storage/session_store.py` → 통과
- `python3 -m unittest tests.test_smoke` → 통과 (`Ran 150 tests`, `OK`)
- `git diff --check -- core/contracts.py storage/session_store.py` → 통과

## 남은 리스크
- 이번 handoff는 storage normalize 경로의 enum validation만 추가했다. UI selector, docs sync,
  fixture trace extension, e2e coverage는 별도 handoff 범위로 남아 있다.
- 작업 전부터 남아 있던 별도 untracked `/work` 파일과 advisory report, verify note 변경은
  이번 handoff 범위가 아니어서 건드리지 않았다.
