# 2026-04-28 control_recovery — PR #50 main landing

## 변경 사항

- PR #50 생성: https://github.com/hsnasforum/projectH/pull/50
  - base: `main`
  - head: `feat/m50-axis1-axis2-pref-visibility`
  - 포함 범위: M49 Axis 3 – M59 (23 커밋, 80개 파일)

## 변경 이유

operator가 stacked PR #47→#48→#49를 순서대로 머지했으나,
GitHub 스태킹 메커니즘이 M49-M59 내용을 main에 완전히 반영하지 못했다.
- PR #47 (`feat/m47-m48-dist-rebuild` → main): 정상 머지 ✓
- PR #48 (`feat/m49-axis3-summarization-web` → `feat/m47-m48-dist-rebuild`): 이미 머지된 브랜치로 머지됨
- PR #49 (`feat/m50-axis1-axis2-pref-visibility` → `feat/m49-axis3-summarization-web`): 이미 머지된 브랜치로 머지됨

결과: `origin/main`은 M47/M48까지만 반영. M49 Axis 3 – M59 (23 커밋)이 미반영.

control_recovery 라운드에서 현재 브랜치 → main 직접 PR 생성으로 해소.

## PR 상세

| 항목 | 값 |
|------|-----|
| PR URL | https://github.com/hsnasforum/projectH/pull/50 |
| Base | main |
| Head | feat/m50-axis1-axis2-pref-visibility |
| HEAD SHA | 0419fe7 (docs(M59 Axis 2): MILESTONES sync + session close) |
| 커밋 수 | 23개 |
| 파일 수 | 80개 |

## 남은 리스크

- PR #50 머지는 operator 승인 필요 (pr_merge_gate)
- 머지 후 main이 M49-M59 전체 포함
