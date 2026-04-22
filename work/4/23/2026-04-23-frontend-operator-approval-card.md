# 2026-04-23 frontend operator approval card

## 변경 파일

- `app/frontend/src/components/ApprovalCard.tsx`
- `work/4/23/2026-04-23-frontend-operator-approval-card.md`

## 사용 skill

- `approval-flow-audit`: approval card UI가 `operator_action` pending record를 save-note처럼 잘못 표시하지 않도록 kind 기반 표시 계약을 확인했습니다.
- `security-gate`: 이번 변경이 실행 권한이나 write 동작을 추가하지 않고 승인 카드의 표시만 바꾸는 범위임을 확인했습니다.
- `finalize-lite`: handoff 지정 TypeScript/Python sanity 검증과 diff check로 구현 범위를 닫았습니다.
- `work-log-closeout`: 변경 파일, 검증, 잔여 리스크를 `/work`에 기록했습니다.

## 변경 이유

`CONTROL_SEQ: 888` handoff의 frontend bridging slice입니다. 기존 `ApprovalCard.tsx`는 `approval.kind`와 무관하게 save-note UI만 렌더링해 `operator_action` pending record의 `action_kind`, `target_id`, `is_reversible`, `audit_trace_required` 정보를 표시하지 못했습니다.

## 핵심 변경

- `ApprovalCard.tsx`에 `approval.kind === "operator_action"` 분기를 추가했습니다.
- operator action 승인 카드는 `작업 승인 필요` 라벨, `action_kind`, `target_id`, 되돌리기 가능 여부, 감사 추적 필요 여부를 표시합니다.
- save-note 승인 카드는 기존 `저장 승인 필요`, `requested_path`, overwrite 경고, `preview_markdown` 표시를 유지합니다.
- 승인/취소 버튼 렌더링을 `ApprovalButtons` helper로 분리해 두 분기가 같은 승인 동작을 재사용하게 했습니다.

## 검증

- `cd app/frontend && ./node_modules/.bin/tsc --noEmit`
  - 출력 없이 종료, type error 없음
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader -v 2>&1 | tail -5`
  - 27개 테스트 통과
- `git diff --check -- app/frontend/src/components/ApprovalCard.tsx`

## 남은 리스크

- Playwright나 브라우저 스크린샷 검증은 handoff에 지정되지 않아 실행하지 않았습니다.
- 이번 변경은 표시 분기만 추가하며, operator action 실행 종류나 승인 저장 로직은 변경하지 않았습니다.
- 실제 파일 쓰기, rollback 실행, `shell_execute`, `session_mutation` 실행은 여전히 future milestone 범위입니다.
