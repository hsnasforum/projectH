STATUS: verified
CONTROL_SEQ: 130
BASED_ON_WORK: work/4/24/2026-04-24-m29-release-gate-milestones.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 131 (M30 direction — M29 loop complete incl. existing activation UX)

---

## M29 Release Gate + MILESTONES.md Closure

### Verdict

PASS. `docs/MILESTONES.md` M29 closure가 `/work` 기술과 일치하고, 재검증 통과.

### Checks Run

- `git diff --check` → OK (출력 없음)
- `rg -n "Milestone 29|M29 closed|Reviewed-Memory Loop|available_to_sync_count|PR #33 merge|M30 direction|M28 structural reminder" docs/MILESTONES.md` → 전체 매칭:
  - `Milestone 29: Reviewed-Memory Loop Refinement` (line 720)
  - `M29 closed` (line 732)
  - `available_to_sync_count > 0` guardrail (line 725)
  - Axes 1–3 shipped infra (lines 728–730)
  - Next 3: PR #33, M30 direction, M28 reminder (lines 736–738)

### What Was Not Checked

- `make e2e-test` 미재실행: docs-only 변경 라운드 (SCOPE_HINT). e2e 144 PASS는 implement 라운드 (seq 130)에서 실행됨.
- unit tests 미재실행: 소스/테스트 파일 미변경.

### Additional Finding: M29 Loop is End-to-End Complete

코드 조사에서 `PreferencePanel.tsx:367–370`에 `pref.status === "candidate"` 조건부 "활성화" 버튼이 이미 존재함을 확인:
- M29 Axis 1 sync → candidate 생성 → PreferencePanel 자동 표시 → 기존 "활성화" 버튼으로 ACTIVE 전환
- reviewed-memory loop (correction adoption → preference candidate → preference active)가 M29 완료 시점에 UI 레벨에서 end-to-end 동작 가능

이 발견은 M30 advisory 질문의 전제를 바꿈: "활성화 UX 추가"는 이미 존재하고, M30의 실제 gap은 TASK_BACKLOG의 cross-session application 또는 prompt injection 수준.

### Docs-only Round Count (same-day, same-family)

오늘 MILESTONES.md 계열 docs-only 라운드:
1. `milestones-priorities-doc-sync` (1번째)
2. `m28-milestones-doc-sync` (2번째)
3. `m29-release-gate-milestones` (3번째) ← 현재

3+ rule 적용 대상. 다음 컨트롤은 advisory_request (docs-only 아님) → rule 위반 없음. 향후 MILESTONES.md 계열 추가 라운드가 필요하면 한 번에 번들로 처리.

### M29 Complete State

| Axis | 내용 | 상태 |
|---|---|---|
| Axis 1 (seq 127) | `sync_adopted_corrections_to_candidates()` + POST endpoint | ✓ |
| Axis 2 (seq 128) | `data-testid="sync-adopted-btn"` UI + inline feedback | ✓ |
| Axis 3 (seq 129) | `available_to_sync_count` + 정확한 버튼 조건 | ✓ |
| Release gate | `make e2e-test` 144 passed (6.6m) | ✓ |
| MILESTONES.md | M29 closed 기록 + Next 3 갱신 | ✓ |
