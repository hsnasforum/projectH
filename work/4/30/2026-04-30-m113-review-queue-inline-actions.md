# 2026-04-30 M113 Review Queue 액션 인라인 이동

## 변경 파일

- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `work/4/30/2026-04-30-m113-review-queue-inline-actions.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 결과 기록 기준을 확인했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1505 지시에 따라 Review Queue 항목의 사유 입력과 액션 버튼을 카드 하단에서 statement/evidence 정보 직후로 옮겨, 긴 context/detail 섹션 때문에 주요 액션 접근이 늦어지는 마찰을 줄였습니다.

## 핵심 변경

- `review-reason-note` textarea와 `review-accept`, `review-edit`, `review-defer`, `review-reject` 버튼 그룹의 JSX 위치를 evidence summary 직후로 이동했습니다.
- `review-context-turns`, `review-detail-toggle`, expanded evidence detail 섹션은 액션 블록 아래로 내려가도록 순서만 재배치했습니다.
- 핸들러, state, className, `data-testid`, 백엔드 로직은 변경하지 않았습니다.
- handoff 제약에 따라 dist 재빌드와 E2E 추가/수정은 수행하지 않았습니다.

## 검증

- `python3 -m py_compile app/handlers/reviewed_memory.py` — PASS
- `rg -n "review-accept|review-defer|review-reject" app/frontend/src/components/ReviewQueuePanel.tsx` — PASS (`review-accept`, `review-defer`, `review-reject` 유지 확인)
- `git diff --check -- app/frontend/src/components/ReviewQueuePanel.tsx` — PASS
- `git diff --name-only -- app/frontend/src/` — PASS (`app/frontend/src/components/ReviewQueuePanel.tsx` 1개만 출력)
- `cd app/frontend && npx tsc --noEmit` — PASS

## 남은 리스크

- `app/static/dist/assets/index.js`는 handoff 제약상 재빌드하지 않았으므로 정적 번들에는 아직 반영되지 않았습니다.
- 브라우저/Playwright 검증은 이번 Axis 1 범위가 아니어서 실행하지 않았습니다. 실제 렌더링 회귀 확인은 후속 Axis 2에서 dist 재빌드와 함께 다루는 것이 맞습니다.
