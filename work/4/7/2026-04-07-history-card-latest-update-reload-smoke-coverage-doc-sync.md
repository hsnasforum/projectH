# history-card latest-update reload smoke coverage doc sync

날짜: 2026-04-07

## 변경 파일

- `README.md` — scenario 18, 19 추가
- `docs/ACCEPTANCE_CRITERIA.md` — latest-update reload + follow-up drift smoke criteria 추가
- `docs/MILESTONES.md` — latest-update reload + follow-up drift smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 24, 25 추가
- `docs/NEXT_STEPS.md` — scenario count 17→19 갱신, latest-update reload + follow-up drift 설명 삽입

## 사용 skill

- 없음 (문서 sync only)

## 변경 이유

- 직전 라운드에서 latest-update reload continuity smoke (scenario 18)를 추가하고, 그 전 라운드에서 follow-up drift prevention smoke (scenario 19)를 추가했으나, 문서 5개가 아직 entity-card reload까지만 반영하고 있었음
- CLAUDE.md Documentation Sync Reminder에 따라 smoke/E2E scenario 변경 시 matching product docs 동기화 필요

## 핵심 변경

- scenario count를 `17`에서 `19`로 갱신 (NEXT_STEPS.md)
- README.md에 scenario 18 (latest-update reload: `최신 확인` badge, `공식+기사 교차 확인` verification, `보조 기사`·`공식 기반` source roles)과 scenario 19 (follow-up drift prevention) 추가
- ACCEPTANCE_CRITERIA.md, MILESTONES.md, TASK_BACKLOG.md에 동일한 내용 반영

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md` — 통과
- grep으로 5개 문서 모두에 latest-update reload 및 follow-up drift 문구 존재 확인
- Playwright / Python regression — 문서 sync only이므로 생략

## 남은 리스크

- 문서 sync만 수행했으므로 runtime/test 회귀 가능성 없음
- noisy community host exclusion variant는 별도 라운드 대상
