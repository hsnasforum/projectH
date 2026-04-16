# reviewed-memory aggregate reload smoke docs parity bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 aggregate-trigger smoke에 hard page reload continuity를 추가했으나, docs parity는 미처리 상태였습니다. Playwright smoke coverage가 변경되면 root docs 동기화가 필요하므로 이번 라운드에서 닫습니다.

## 핵심 변경

1. **`README.md`** (scenario 12): `reversed` + `conflict_visibility_checked` 상태 후 hard page reload 시 `검토 메모 적용 후보` section, `충돌 확인 완료`/`적용 되돌림 완료` badge, helper text, payload continuity 검증 추가 기술.
2. **`docs/MILESTONES.md`** (line 55): aggregate smoke 설명 끝에 hard page reload continuity 검증 추가 기술.
3. **`docs/ACCEPTANCE_CRITERIA.md`** (line 117): lifecycle records 설명에 hard page reload 후 aggregate-trigger UI 정합 요구 추가.
4. **`docs/TASK_BACKLOG.md`** (line 196): conflict-visibility 설명 끝에 hard page reload continuity 검증 추가 기술.

## 검증

- `rg -n 'hard page reload|reload.*reversed.*conflict|reload.*검토 메모 적용 후보' README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs` → 4개 docs + 1개 smoke 파일에서 reload continuity 매치 확인
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/16` → clean
- test 미재실행: docs-only truth-sync 라운드이며, 이전 라운드에서 isolated Playwright rerun (1 passed, 50.6s)이 이미 확인됨

## 남은 리스크

- `docs/NEXT_STEPS.md`는 이번 scope에서 제외했습니다. 직접적인 모순이 발견되지 않았으며, handoff에서도 불필요 시 생략 가능으로 명시했습니다.
- `docs/PRODUCT_SPEC.md`는 handoff target에 포함되지 않았으나, aggregate lifecycle 설명이 상세하므로 추후 필요시 별도 동기화 가능합니다.
