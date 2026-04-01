# 2026-04-01 overwrite approval execution docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- `verify/4/1/2026-04-01-overwrite-approval-execution-verification.md` 기준으로, overwrite approval execution 코드는 shipped이지만 docs에는 아직 "Not Implemented" / "Explicitly Deferred"로 남아있어 truth가 어긋남.
- same-family 안의 가장 작은 current-risk reduction인 docs truth sync.

## 핵심 변경
- `README.md` Safety Defaults: overwrite 기본 거부 + explicit approval 시 덮어쓰기 실행 설명 추가
- `docs/PRODUCT_SPEC.md`:
  - Approval Rules Implemented: overwrite approval execution의 현재 shipped behavior 설명 추가 (pending approval `overwrite: true`, UI 경고, `allow_overwrite` 실행)
  - Not Implemented에서 `overwrite approval execution` 항목 제거
- `docs/ACCEPTANCE_CRITERIA.md`:
  - Not Implemented에서 `overwrite approval execution` 항목 제거
  - Approval And Safety Gates Implemented: reissue 시 overwrite 경고 + explicit overwrite 실행 + 로그 기록 설명 추가
  - Open Questions에서 "Should overwrite ever become an explicit future approval path?" 제거 (이미 구현됨)
- `docs/NEXT_STEPS.md`: Explicitly Deferred에서 `overwrite approval execution` 항목 제거
- `docs/TASK_BACKLOG.md`: Not Implemented에서 `overwrite approval execution` 항목 제거

## 검증
- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`: 통과
- docs-only round이므로 Python/browser 검증은 실행하지 않음

## 남은 리스크
- docs-only 변경이므로 기능적 리스크 없음
- reissue 경로의 기존 경고 문구("이미 파일이 있으므로 다른 저장 경로로 다시 요청해 주세요")는 코드에 남아있으나, docs에는 현재 shipped behavior만 반영. 문구 완화는 별도 판단.
- overwrite approval execution family는 코드 + docs sync까지 truthfully 닫힘
