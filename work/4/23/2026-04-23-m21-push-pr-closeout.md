# 2026-04-23 M21 Push + PR Closeout (operator_retriage seq 91)

## 변경 파일
- `docs/MILESTONES.md` — M20 Axis 3 + M21 Axes 1–3 closed 항목 추가

## 배경
- CONTROL_SEQ 91 `commit_push_bundle_authorization + internal_only`
- PR #31 (M13 Axis 6–M17 Axis 3) 상태 재확인: 실제로 MERGED (state: MERGED, mergeCommit 확인됨)
- operator_request.md에 Draft 대기 중으로 기재되었으나 stale — 현재 GitHub 상태가 truth
- stacked PR 복잡성 없음: PR #31 이미 merged이므로 feat/watcher-turn-state → main 직접 push + PR 가능

## 실행 내용

### doc-sync (commit 6fc42e2)
- `docs/MILESTONES.md`: M20 Axis 3 shipped 항목 추가 (seq 84/85, 142 passed 7.5m)
- `docs/MILESTONES.md`: M21 Axes 1–3 shipped + "Milestone 21 closed" 추가 (seq 87/90/91, 142 passed 8.3m)
- M20 shipped header "Axes 1-2" → "Axes 1-3" 업데이트
- `git diff --check` → OK

### push
- `git push origin feat/watcher-turn-state`
- push result: c7b658d..6fc42e2 → OK

### PR 생성
- **PR #32**: https://github.com/hsnasforum/projectH/pull/32
- title: feat: M20 Axis 2–3 and M21 Axes 1–3 — conflict detection, correction lifecycle, global reject (seqs 82–91)
- base: main, head: feat/watcher-turn-state
- 커버리지: M20 Axis 2 (seq 82), M20 Axis 3 smoke gate (seq 84/85), M21 Axis 1 (seq 87), M21 Axis 2 (seq 90), M21 Axis 3 gate (seq 91), doc-sync (6fc42e2)

## 검증 (이전 verify 라운드에서 이미 실행)
- `make e2e-test` M20 Axis 3: 142 passed (7.5m)
- `make e2e-test` M21 Axis 3: 142 passed (8.3m)
- 모든 단위 테스트 OK (29+26 preference/sqlite tests)

## 남은 리스크
- PR #32 merge: operator 승인 대기
- Global reject Playwright 커버리지 없음 (M21 Axis 2 boundary 기준 deferred) — M22 후보
- `SQLiteCorrectionStore._transition()` 상태 순서 강제 없음 — M22 후보
- report/gemini/ untracked 3개 파일: operator 지시 없으면 그대로 유지

## 다음 control
- `.pipeline/advisory_request.md` CONTROL_SEQ 92 — M22 scope 정의
