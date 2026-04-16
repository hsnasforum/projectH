# 2026-04-16 controller idle roam deterministic smoke docs sync

## 변경 파일
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 idle roam bounds/desk-exclusion deterministic smoke 시나리오 6번(`window.testPickIdleTargets` + `window.getRoamBounds`)과 controller-local test hook이 이미 구현되었고, `controller/index.html`, `e2e/tests/controller-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`에는 해당 커버리지가 반영되어 있었습니다.
- 그러나 `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 controller smoke 설명에는 idle roam bounds/desk-exclusion smoke 커버리지 언급이 누락되어 있었습니다.
- 이번 슬라이스는 두 docs 파일의 controller smoke 설명을 현재 shipped truth에 맞추는 docs-only sync입니다.

## 핵심 변경
- `docs/MILESTONES.md` line 27: controller smoke 목록에 `deterministic idle roam bounds/desk-exclusion safety via window.testPickIdleTargets + window.getRoamBounds test hooks` 추가
- `docs/TASK_BACKLOG.md` line 11: 동일 내용 추가

## 검증
- `make controller-test`
  - 결과: `6 passed (5.5s)` — 기존 6개 시나리오 모두 통과
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `make e2e-test` full browser suite 생략. 이번 변경은 docs-only이며 코드나 브라우저 계약 변경 없음.

## 남은 리스크
- 이번 smoke는 bounds/desk-exclusion 안전 계약만 검증합니다. docs에 설명된 나머지 roam 휴리스틱(inter-agent proximity, graduated history penalty, free-walk 비율, stale-position timer, micro-drift, glance 등)은 이 deterministic assertion 범위 밖입니다.
- controller는 내부 operator 도구이므로 test hook 노출의 보안 위험은 낮습니다.
