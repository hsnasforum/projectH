# 2026-04-22 Milestone 9 operator action contract

## 변경 파일
- `core/contracts.py`
- `work/4/22/2026-04-22-milestone9-operator-action-contract.md`

## 사용 skill
- `finalize-lite`: 필수 체크 통과 여부, 문서 동기화 범위, `/work` closeout 준비 상태를 구현 종료 전에 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 866이 Milestone 9 "Approval-Gated Local Operator Foundation"의 첫 데이터 계약 slice를 요구했습니다.
- 실행 연결 전 단계로, 승인 게이트가 필요한 local operator action의 audit/rollback 기대값을 공유 계약에 먼저 정의해야 했습니다.

## 핵심 변경
- `core/contracts.py`에 `TypedDict` import를 추가했습니다.
- `CandidateReviewSuggestedScope` 뒤에 `OperatorActionKind` StrEnum을 추가했습니다.
- `OperatorActionKind` 값으로 `local_file_edit`, `shell_execute`, `session_mutation` 3가지를 정의했습니다.
- `OperatorActionContract` `TypedDict(total=False)`를 추가하고 `action_kind`, `target_id`, `requested_at`, `audit_trace_required`, `is_reversible` 5개 필드를 정의했습니다.
- handoff 제약에 따라 storage, agent loop, tests, docs, fixtures 파일은 수정하지 않았습니다.

## 검증
- `python3 -m py_compile core/contracts.py` -> 통과
- `python3 -m unittest tests.test_eval_loader -v` -> 9개 테스트 통과
- `git diff --check -- core/contracts.py` -> 통과

## 남은 리스크
- 이번 라운드는 데이터 계약만 추가했으며 operator action 실행, 승인 플로우, 저장소 연결은 구현하지 않았습니다.
- 문서 동기화는 handoff 범위 밖이라 수행하지 않았습니다. 필요하면 별도 verify/handoff 라운드에서 판단해야 합니다.
