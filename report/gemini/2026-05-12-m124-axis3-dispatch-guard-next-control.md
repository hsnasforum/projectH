# Advisory CONTROL_SEQ 1617 — post dispatch-guard next control

**Date:** 2026-05-12
**Request:** `.pipeline/advisory_request.md` CONTROL_SEQ 1617
**Advisory owner:** Claude

---

## Request summary

After CONTROL_SEQ 1616 (Codex dispatch pasted-content guard, unit-verified), choose one
exact next control action among:
1. implement `<bounded pipeline-runtime current-risk slice>`
2. switch_axis `<next product/runtime axis>`
3. operator_required `<one decision>`

---

## Current truth

| Item | Status |
|------|--------|
| CONTROL_SEQ 1616 dispatch guard | PASS — 30 unit tests, py_compile, git diff --check |
| Live tmux launcher smoke | 미실행 (residual risk, operational) |
| M124 Axis 3 dirty bundle | tests/test_smoke.py + docs/MILESTONES.md + docs/TASK_BACKLOG.md — impl + doc-sync 완료 |
| Dispatch guard dirty bundle | lane_surface.py + watcher_dispatch.py + tests/test_watcher_core.py — uncommitted |
| M125 direction | 미확정 — advisory 결정 대기 |

---

## Candidate evaluation

**1. implement `<pipeline-runtime current-risk slice>`**

Dispatch-stall 패밀리(pasted-content 누적)는 단위 테스트 수준에서 닫혔다.
잔여 리스크(live launcher 미재로드)는 운영 조치(런처 재시작)이지 코드 변경 슬라이스가 아니다.
새로운 bounded pipeline-runtime 슬라이스가 operator publish보다 명확히 안전한 상황이 아니다.
→ **기각**: 추가 implement 슬라이스 없음.

**2. switch_axis `<product/runtime axis>`**

M125 방향은 docs/work/verify 어디에도 확정된 evidence가 없다.
advisory_request 경계: "M125 direction as unselected unless current docs/work/verify support one exact next slice."
→ **기각**: M125 unselected, switch 근거 없음.

**3. operator_required**

- M124 Axis 3 dirty bundle: commit/push/draft PR = operator boundary (publish).
- Dispatch guard dirty bundle: commit/push/draft PR = operator boundary (publish).
- 두 bundle 모두 구현·검증이 완료되어 operator 승인만 대기.
→ **채택**.

---

## Recommendation

`operator_required`: M124 Axis 3 + dispatch guard publish bundle authorization

### Bundle 1 — M124 Axis 3

| 파일 | 내용 |
|------|------|
| `tests/test_smoke.py` | 수렴 벤치마크 fixture 3개 (+3, 166→169) |
| `docs/MILESTONES.md` | Axis 3 완료 + M124 아크 종료 요약 + Next 3 M125 갱신 |
| `docs/TASK_BACKLOG.md` | #150 Axis 3 + #151 아크 종료 항목 |

Branch: `feat/m124-axis3-convergence-benchmark-expansion`
Base: `feat/m124-axis2-investigation-quality-summary` (PR #126)
Expected: Draft PR #127

### Bundle 2 — Pipeline dispatch guard

| 파일 | 내용 |
|------|------|
| `pipeline_runtime/lane_surface.py` | `pane_text_has_unsubmitted_pasted_content()` |
| `watcher_dispatch.py` | single-submit dispatch + `prompt_contains_pasted_content` defer |
| `tests/test_watcher_core.py` | 반복 Enter 방지 + pending re-paste 방지 회귀 테스트 |

Branch: `feat/pipeline-dispatch-pasted-content-guard`
Base: main (pipeline-runtime 전용, product 스택 무관)

---

## Confidence: high

Evidence: verify CONTROL_SEQ 1617 (both bundles unit-verified), MILESTONES confirms M125 unselected.
No bounded implement slice is safer before the operator boundary.

---

## Next step

`operator_request.md` CONTROL_SEQ 1618:
authorize M124 Axis 3 publish bundle + dispatch guard publish bundle
(`commit_push_bundle_authorization + internal_only` × 2)
