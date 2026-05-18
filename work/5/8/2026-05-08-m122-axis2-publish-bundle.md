# 2026-05-08 M122 Axis 2 publish bundle

## 변경 파일

- `core/contracts.py` (커밋 6bead0b)
- `core/web_claims.py` (커밋 6bead0b)
- `core/agent_loop.py` (커밋 6bead0b)
- `tests/test_smoke.py` (커밋 6bead0b)
- `docs/MILESTONES.md` (커밋 6bead0b)
- `docs/TASK_BACKLOG.md` (커밋 6bead0b)
- `work/5/8/2026-05-08-m122-axis2-publish-bundle.md`

## 사용 skill

- `round-handoff`: operator_retriage 역할에서 commit/push/PR 실행 후 /work 클로즈아웃과 다음 컨트롤 작성.

## 변경 이유

- M122 Axis 2 구현 + doc-sync 모두 검증 완료(CONTROL_SEQ 1573)된 6개 파일을 커밋/push/PR로 publish했다.
- operator_retriage 지시에 따라 `commit_push_bundle_authorization + internal_only` + `pr_creation_gate + gate_24h`를 이 라운드에서 직접 처리했다.

## 핵심 변경

- 신규 브랜치 `feat/m122-axis2-unresolved-separation`을 `origin/feat/m122-axis1-multiSource-agreement`(`23d9e9c`) 기준으로 생성했다.
  - 로컬 HEAD와 origin 트리 일치 확인 (`git diff --stat` 출력 없음).
- 6개 파일 staged + commit `6bead0b`:
  - `core/contracts.py`, `core/web_claims.py`, `core/agent_loop.py`, `tests/test_smoke.py`: M122 Axis 2 구현
  - `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`: M122 Axis 2 doc-sync
- `git push origin feat/m122-axis2-unresolved-separation` — PASS
- Draft PR #120 생성: `feat/m122-axis2-unresolved-separation` → base `feat/m122-axis1-multiSource-agreement`

## publish 결과

| 항목 | 결과 |
|------|------|
| 커밋 SHA | `6bead0b` feat(investigation): UNRESOLVED status separation for entity-card (M122 Axis 2) |
| 브랜치 | `feat/m122-axis2-unresolved-separation` |
| PR | #120 — draft, base: `feat/m122-axis1-multiSource-agreement` |
| PR URL | https://github.com/hsnasforum/projectH/pull/120 |

**parent/child 연결:** PR #120(M122 Axis 2)은 PR #119(M122 Axis 1, OPEN) 위의 스택. PR #119가 병합되면 PR #120 base를 `feat/m121-watcher-lease-reclamation`으로, 이후 cascade 완료 시 main으로 retarget 예정.

## 남은 리스크

- M122 Axis 3: `core/agent_loop.py` line 4374 이후 display/hint 함수에 UNRESOLVED 레이블 전파 필요
  - `_claim_coverage_status_rank()` — UNRESOLVED → return 0
  - `_claim_coverage_status_label()` — UNRESOLVED → "미해결"
  - `_build_claim_coverage_progress_summary()` unresolved_slots 집합 — UNRESOLVED 추가
- PR #119-#120 스택이 main으로 cascade merge될 때 retarget 필요
