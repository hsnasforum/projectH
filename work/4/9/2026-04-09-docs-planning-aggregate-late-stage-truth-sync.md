# docs: NEXT_STEPS MILESTONES TASK_BACKLOG aggregate late-stage truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — line 419: "keep the other transition actions contract-only" → "now also shipped" 수정
- `docs/MILESTONES.md` — line 340: `effect_active` 이후 stop-apply/reversal/conflict-visibility 추가
- `docs/TASK_BACKLOG.md` — line 147: `effect_active` 이후 3단계 추가; line 717: reversal/conflict-visibility 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 권위 문서(PRODUCT_SPEC, ARCHITECTURE, ACCEPTANCE_CRITERIA)는 이미 전체 라이프사이클 반영
- 기획 문서만 `effect_active`에서 끝나거나 "contract-only"로 기술하여 출하 현실과 모순
- `docs/PRODUCT_SPEC.md:1531-1537`과 `e2e/tests/web-smoke.spec.mjs:900-966`에서 전체 흐름 출하 확인

## 핵심 변경
- NEXT_STEPS: contract-only 표기 → shipped 표기
- MILESTONES: `effect_active` 이후 적용 중단/되돌리기/충돌 확인 추가
- TASK_BACKLOG: 2곳에서 누락된 후반 단계 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 4줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 기획 문서도 aggregate 전체 출하 라이프사이클 반영 완료
