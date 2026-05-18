# 2026-04-29 M98 docs 번들

## 변경 파일

- `README.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/PRODUCT_SPEC.md`
- `work/4/29/2026-04-29-m98-docs-bundle.md`

## 사용 skill

- `doc-sync`: M98 Axis 1/2 구현 사실을 현재 제품 문서와 수락 기준에 맞춰 반영했다.
- `finalize-lite`: docs-only 라운드의 검증 범위와 미실행 항목을 정리했다.
- `work-log-closeout`: 변경 파일, 실행 명령, 남은 리스크를 현재 `/work` 형식으로 기록했다.

## 변경 이유

- M98 Axis 1 교정 이력 상세 조회와 Axis 2 dist 재빌드가 완료되어, 현재 구현 상태와 문서 설명 사이의 drift를 줄였다.
- handoff CONTROL_SEQ 1443에서 지정한 5개 문서 파일만 대상으로 삼고 코드, dist, E2E 파일은 추가 수정하지 않았다.

## 핵심 변경

- `README.md` Current Product Slice에 `GET /api/corrections/<correction_id>` 기반 교정 상세 패널을 추가했다.
- `docs/MILESTONES.md`에 M98 교정 이력 상세 조회 Axis 1과 dist rebuild Axis 2 완료 기록을 추가하고 다음 우선순위 문구를 M98 후속 상태로 갱신했다.
- `docs/TASK_BACKLOG.md` 상단 next phase target 요약에 M98 Axis 1-2 완료 사실을 반영했다.
- `docs/ACCEPTANCE_CRITERIA.md`에 `fetchCorrectionDetail()`, `data-testid="correction-detail-panel"`, Playwright smoke coverage 항목을 추가하고 smoke coverage count를 127로 갱신했다.
- `docs/PRODUCT_SPEC.md`에 read-only correction history detail API와 PreferencePanel 상세 패널 UX 설명을 추가했다.

## 검증

- 통과: `git diff --check -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
- 통과: `rg -n "correction-detail-panel|fetchCorrectionDetail|GET /api/corrections/<correction_id>|M98 Axis 1-2|M98 교정 이력 상세 조회" README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
- 통과: `git diff --stat -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
- 미실행: 코드 테스트와 Playwright E2E는 이번 handoff가 docs-only 라운드라 실행하지 않았다.

## 남은 리스크

- Playwright 시나리오 `correction list item click shows correction detail panel`의 실제 브라우저 실행은 여전히 CI 확인 대상이다.
- M98 전체 dirty tree에는 Axis 1 source/E2E와 Axis 2 dist 변경이 함께 남아 있으며, 이번 라운드는 docs 동기화만 수행했다.
- commit/push/PR 생성은 implement lane 범위 밖이라 수행하지 않았다.
