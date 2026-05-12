# 2026-04-27 TASK_BACKLOG E2E gap note

## 변경 파일
- `docs/TASK_BACKLOG.md`
- `work/4/27/2026-04-27-task-backlog-e2e-gap-note.md`

## 사용 skill
- `doc-sync`: M47/M48 A2 E2E 커버리지 공백과 현재 빌드 산출물 블로커를 TASK_BACKLOG에 반영하는 범위를 확인했다.
- `work-log-closeout`: 이번 implement lane의 변경, 검증, 남은 리스크를 한국어 closeout으로 정리하는 데 사용했다.

## 변경 이유
- CONTROL_SEQ 519 handoff는 이전 E2E 슬라이스가 `app_preview_static_dist_stale` / `e2e_boundary_requires_unallowed_build_asset_update`로 막힌 사실을 `docs/TASK_BACKLOG.md`에 기록하라고 지시했다.
- 이 기록이 없으면 다음 세션에서 M47 "신뢰도 높음" 집계 헤더와 M48 Axis 2 "충돌 위험" 헤더 E2E 작업이 같은 정적 dist 블로커를 반복할 수 있다.

## 핵심 변경
- `docs/TASK_BACKLOG.md`의 `M48 Direction Candidates` 아래에 `M47/M48 A2 E2E 커버리지 갭 (post-merge 작업)` 섹션을 추가했다.
- M47 "신뢰도 높음" 집계 헤더와 M48 Axis 2 `data-testid="high-severity-conflict-count"` 헤더에 대한 E2E 테스트가 아직 없음을 명시했다.
- M46 "고품질" 집계 헤더 E2E는 `e2e/tests/web-smoke.spec.mjs` line 11674에 존재한다고 기록했다.
- `app/static/dist`가 git-tracked이고 `app/frontend/package.json`에 build 스크립트가 없어, dist 재빌드 없이는 해당 렌더링을 E2E로 확인할 수 없다는 블로커를 남겼다.
- PR #45 merge 후 Vite 직접 빌드, M47/M48 A2 mock-route E2E 추가, 재빌드된 dist와 테스트 커밋 순서를 후속 작업으로 적었다.

## 검증
- `sha256sum .pipeline/implement_handoff.md && sed -n '1,220p' .pipeline/implement_handoff.md`로 handoff SHA `d0e1206568952e71976f926d5cf88e9788324f8a72b68b78ecaf772740bb8d39`와 CONTROL_SEQ 519를 확인했다.
- `sed -n '1,220p' work/4/27/2026-04-27-m48-axis2-round-closeout.md`로 기반 work note를 확인했다.
- `sed -n '1,220p' verify/4/27/2026-04-27-m48-axis2-round-closeout.md`로 기반 verify note를 확인했다.
- `git diff --check -- docs/TASK_BACKLOG.md` 통과.
- `grep -n "M47/M48 A2 E2E\|high-severity-conflict-count\|신뢰도 높음.*E2E\|app/static/dist" docs/TASK_BACKLOG.md` 통과.
- `git diff --check -- docs/TASK_BACKLOG.md work/4/27/2026-04-27-task-backlog-e2e-gap-note.md` 통과.

## 남은 리스크
- 이번 라운드는 문서 기록만 수행했으며 코드, dist, E2E 테스트는 수정하지 않았다.
- 실제 M47/M48 A2 E2E 커버리지는 PR #45 merge 이후 `app/static/dist` 재빌드와 mock-route 테스트 추가가 함께 수행되어야 한다.
- commit, push, branch/PR publish, merge는 수행하지 않았다.
