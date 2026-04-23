# 2026-04-23 PR creation authority arbitration

## 배경
- PR #27이 `1b23edf`에서 merge된 후, 로컬 브랜치 `feat/watcher-turn-state`에 5개의 추가 커밋(seq 1, 5, 6 관련)이 생성됨.
- `operator_request` (CONTROL_SEQ 5)에서 이미 `pr_merge_gate` 승인이 있었으나, HEAD mismatch로 인해 런타임이 `recovery` 상태로 진입하며 canonical `control = none`으로 해소됨.
- 현재 5개 커밋은 검증 완료(355/355 tests OK) 상태이나, `main` 병합을 위한 열린 PR이 없음.

## 판단
- **RECOMMEND: Option A (Direct Draft PR Creation by Verify/Handoff Owner)**
- **근거**:
  1. **연속성 및 의도 존중**: 이전 `pr_merge_gate`를 통해 이미 operator의 병합 의사가 확인됨. 현재의 `head_mismatch`는 기술적 격차일 뿐이며, 이를 메우기 위한 PR 생성은 "ordinary recovery" 범위에 해당함.
  2. **CLAUDE.md 예외 조항 준수**: `CLAUDE.md`는 `pr_creation_gate` 성격의 follow-up에 대해 verify/handoff 라운드에서 draft PR을 직접 생성하는 것을 허용함.
  3. **비파괴적 투명성**: Draft PR 생성은 그 자체로 파괴적이지 않으며, operator가 최종 merge gate(`pr_merge_gate`)에서 전체 diff를 다시 확인할 수 있는 기회를 제공함.
  4. **Auditable Publish**: `GEMINI.md` 가이드에 따라, 이미 의사가 확인된 건에 대해서는 operator 재호출보다 에이전트 간 논의를 통해 auditable한 정리를 마치는 쪽을 우선함.

## 권고 실행 가이드
1. **Verify/Handoff Owner (Claude)**: 현재 HEAD(`3968fab`) 기준으로 `main` 대상의 새 draft PR을 생성함.
2. **Dirty Worktree 처리**: `pipeline_gui/` 관련 dirty 파일들은 이번 검증 범위 밖이므로, PR 생성 시 포함되지 않도록 주의함 (staged 상태가 아니면 `gh pr create` 시 반영되지 않음).
3. **후속 제어**: PR 생성 후 URL을 `/work` 또는 `/verify`에 기록하고, `.pipeline/operator_request.md`를 통해 새 `pr_merge_gate` (HEAD: `3968fab`)를 작성하여 최종 병합 승인을 요청함.

## 남은 리스크
- `pipeline_gui/` 변경분이 의도치 않게 PR에 섞이지 않도록 branch state를 엄격히 분리해야 함.
- 새 PR 생성 후 런타임이 `pr_merge_gate`를 다시 올바르게 인식하는지 live runtime status 확인 필요.
