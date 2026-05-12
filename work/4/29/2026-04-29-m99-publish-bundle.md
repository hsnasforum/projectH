# 2026-04-29 M99 advisory-loop-recovery-guard 번들 publish

## 변경 파일

- `watcher_core.py`
- `watcher_prompt_assembly.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/harness/advisory.md`
- `.pipeline/README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/4/29/2026-04-29-m99-publish-bundle.md`

## 실행 내용

- `operator_request.md` CONTROL_SEQ 1446 (`commit_push_bundle_authorization + internal_only + pr_creation_gate`)를
  operator_retriage 라운드에서 직접 처리했다.
- 브랜치 명칭: operator_request의 `fix/advisory-loop-recovery-guard`에서
  `fix/m99-advisory-loop-recovery-guard`로 일관성 수정 (m-prefix 컨벤션 준수).
- PR #91 (M98, `feat/m98-axis1-correction-history`)이 draft 대기 중이므로 OUTPUTS 스태킹 규칙에 따라
  parent branch `feat/m98-axis1-correction-history`를 base로 사용.
- `git checkout -b fix/m99-advisory-loop-recovery-guard` → `git add` (10개 파일 exact) → `git commit` → `git push`

## 결과

| 항목 | 결과 |
|------|------|
| 커밋 SHA | `9331c5b` |
| 브랜치 | `fix/m99-advisory-loop-recovery-guard` |
| push | ✓ `origin/fix/m99-advisory-loop-recovery-guard` |
| PR 생성 | ✓ [#92](https://github.com/hsnasforum/projectH/pull/92) — draft, base: `feat/m98-axis1-correction-history` |
| 변경 통계 | 10 files changed, 160 insertions(+), 4 deletions(-) |

## 스태킹 링크

- parent: `feat/m98-axis1-correction-history` (PR #91, draft, base `feat/m96-bundle`)
- child: `fix/m99-advisory-loop-recovery-guard` → PR [#92](https://github.com/hsnasforum/projectH/pull/92) (draft)
- PR #91 머지 후 child PR을 `feat/m96-bundle` 또는 `main`으로 retarget

## 남은 리스크

- PR #91 (M98) + PR #92 (M99) 모두 draft, `pr_merge_gate` operator 대기
- PR #92 머지 후 `feat/m96-bundle` 또는 `main`으로 retarget 필요
- 브라우저 E2E / 장시간 soak 미실행 (watcher-only 변경)
- M100 다음 슬라이스 방향 advisory 대기 (CONTROL_SEQ 1448)
