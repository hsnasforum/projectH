# 2026-04-22 claim coverage source role tooltip

## 변경 파일
- `app/frontend/src/components/MessageBubble.tsx`
- `tests/test_smoke.py`
- `work/4/22/2026-04-22-claim-coverage-source-role-tooltip.md`

## 사용 skill
- `investigation-quality-audit`: entity-card claim coverage의 source-role 표시가 보조 web investigation 품질 범위 안에 있는지 확인했습니다.
- `security-gate`: 변경이 read-only UI 표시와 serializer 회귀 테스트에 한정되고 승인/write/storage 경계를 바꾸지 않는지 확인했습니다.
- `doc-sync`: UI behavior 변경에 따른 문서 동기화 필요성을 점검했으며, 이번 handoff 제약상 docs는 수정하지 않았습니다.
- `finalize-lite`: 구현 종료 전 실행한 검증과 남은 리스크를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 771의 exact slice에 따라 claim coverage badge가 각 slot을 뒷받침하는 `source_role`을 사용자에게 드러내도록 했습니다.
- `source_role`은 이미 backend payload와 frontend type에 존재하므로 display layer와 serializer 회귀 테스트만 보강했습니다.

## 핵심 변경
- `MessageBubble.tsx`의 claim coverage badge `<span>`에 `title` tooltip을 추가해 `item.source_role`이 있을 때 source-role label을 노출했습니다.
- `source_role`이 없거나 빈 값이면 `title`을 `undefined`로 두어 기존 badge 렌더링과 동일하게 동작하게 했습니다.
- 기존 `isTrustedWeak` 판단, badge className 분기, status suffix 렌더링은 변경하지 않았습니다.
- `test_serialize_claim_coverage_includes_source_role`을 추가해 `_serialize_claim_coverage()`가 `source_role`을 유지하는지 검증했습니다.

## 검증
- `python3 -m py_compile app/serializers.py` 통과
- `python3 -m unittest tests.test_smoke` 통과 (`150 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 라운드는 commit/push/PR을 수행하지 않았습니다.
- handoff 제약에 따라 docs, `app/serializers.py`, `app/frontend/src/types.ts`, `core/`, pipeline control 파일은 수정하지 않았습니다.
- Playwright/browser 검증은 handoff 필수 검증에 포함되지 않았고, 이번 변경은 tooltip-only 표시라 실행하지 않았습니다.
- 작업 시작 전부터 선행 라운드의 dirty tree가 남아 있어 전체 diff/status에는 이번 변경 외 파일들이 함께 보입니다.
