# 2026-04-15 review-queue reject defer expansion

## 추천 슬라이스
`review-queue action-vocabulary expansion: reject and defer`

## 추천 이유
- **전략적 정렬**: `reviewed-memory` 패밀리의 "visible lifecycle parity" 가이드레일이 dense하게 구축되어 안정성이 확보되었습니다. 이제 마일스톤 7에서 계획된 `accept`-only 리뷰 큐의 기능적 확장을 시작할 시점입니다.
- **기능적 필연성**: `reject`(dismissal)와 `defer`(later revisit)는 검토 후보 큐가 "수락 전용" 또는 "무한 증식" 상태에 머물지 않도록 하는 필수적인 종료 경로입니다.
- **구현 효율성**: 기존 `candidate_review_record` 및 `POST /api/candidate-review` 인프라를 그대로 재사용하며, `edit`과 달리 복잡한 텍스트 편집 UI가 필요 없어 surgical한 확장이 가능합니다.
- **리스크 통제**: 이 슬라이스는 여전히 "reviewed-but-not-applied" 원칙을 유지하며, 사용자 레벨 메모리 쓰기를 열지 않으므로 안전합니다.

## 핵심 범위
- `core/contracts.py`: `CandidateReviewAction` (REJECT, DEFER) 및 `CANDIDATE_REVIEW_ACTION_TO_STATUS` 맵 확장
- `app/handlers/aggregate.py`: `submit_candidate_review`의 `ACCEPT` 전용 제한 해제 및 신규 액션 처리
- `app/templates/index.html`: `검토 후보` 아이템 UI에 `거절`, `보류` 버튼 추가
- `app/static/app.js`: 신규 버튼 액션 바인딩 및 API 연동
- `tests/test_web_app.py`: `reject`, `defer` 액션 결과 및 큐 이탈 로직 검증 추가
- `e2e/tests/web-smoke.spec.mjs`: 신규 버튼 노출 및 동작 브라우저 스모크 추가

## 제외 범위
- `edit` 액션 (리뷰 시 문구 수정 UI)
- `reviewed-memory store` (사용자 레벨 메모리 직접 쓰기)
- `repeated-signal promotion` (차단된 집계 해제)

## 결론
Codex는 이 권고를 바탕으로 `.pipeline/claude_handoff.md`를 직접 작성하여 구현 라운드를 시작할 수 있습니다.
