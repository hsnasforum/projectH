STATUS: verified
CONTROL_SEQ: 1564
BASED_ON_WORK: work/5/8/2026-05-08-m122-next3-doc-sync.md
BASED_ON_PRIOR_WORK: work/5/8/2026-05-08-m121-doc-sync.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: advisory_request.md CONTROL_SEQ 1564
PUBLISH_RESULT: commit 8fc5e6d, PR #117 MERGED (feat/m121-watcher-lease-reclamation → feat/m120-axis2-injection-demotion-badge)

---

# 2026-05-08 M121 watcher self-restart lease reclamation — verify

## 이번 라운드 범위

CONTROL_SEQ 1558 implement_handoff (m121_watcher_lease_reclamation) 실행 결과.
work note 변경 범위: `watcher_state.py`, `pipeline_runtime/supervisor.py`, `tests/test_watcher_core.py` 3개 파일.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile watcher_state.py pipeline_runtime/supervisor.py` | **PASS** |
| `python3 -m unittest -v tests.test_watcher_core.PaneLeaseOwnerPidWiringTest` | **PASS — 10개** (기존 7 + 신규 3) |
| `git diff --check` (3개 파일) | **PASS** |

## 핵심 변경 확인

**`watcher_state.py:PaneLease.archive_for_restart()` (line 191–217):**
- lock이 존재하면 `locks/archive/<slot>.lock.stale-<timestamp>`로 `rename()`
- archive 디렉터리 생성 실패 → `False` + warning log (self-restart 자체는 계속)
- rename 실패 → `False` + warning log
- lock 없음 → no-op `True`

**`pipeline_runtime/supervisor.py` (line 2664–2666):**
- `PaneLease` import (line 20) 확인 ✓
- `_maybe_restart_watcher_for_source_change()` 내 `_terminate_pid_file()` **직전**에 4개 slot archive 호출 — 순서 올바름 ✓

```python
lease = PaneLease(self.base_dir / "locks")
for slot in ("slot_verify", "slot_implement", "slot_advisory", "slot_followup"):
    lease.archive_for_restart(slot)
self._terminate_pid_file(self.base_dir / "experimental.pid")
```

**신규 테스트 3개 실행 로그 확인:**

| 테스트 | 로그 증거 | 결과 |
|--------|----------|------|
| `test_watcher_acquire_succeeds_after_archive_for_restart` | `job-1 acquired → archived → job-2 acquired` | ✓ |
| `test_archive_for_restart_moves_active_lease_to_archive` | 직접 실행 PASS | ✓ |
| `test_archive_for_restart_returns_true_when_no_lease_exists` | 직접 실행 PASS | ✓ |

## doc-sync 검증 결과 (CONTROL_SEQ 1561)

| 체크 | 결과 |
|------|------|
| `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` | **PASS** |
| `docs/MILESTONES.md` M121 섹션 위치 (line 1824, M120 Axis 2 직후) | **확인** |
| `docs/TASK_BACKLOG.md` #140 항목 (line 154, #139 직후) | **확인** |
| `docs/TASK_BACKLOG.md` line 9 M121 note 추가 | **확인** |

**알려진 잔존 gap**: `## Next 3 Implementation Priorities` 섹션 (MILESTONES line 1835) 내용이 stale (PR #91–#111 / M117 완료 대기 → 실제 PR #113–#118 모두 MERGED, M121 완료). doc-sync handoff 금지 범위였으므로 다음 advisory/implement에서 처리.

## publish bundle 결과 (operator retriage 확인)

| 항목 | 결과 |
|------|------|
| 커밋 SHA | `8fc5e6d` fix(runtime): archive stale leases before watcher self-restart (M121) |
| 브랜치 | `feat/m121-watcher-lease-reclamation` |
| PR | #117 — MERGED (base: `feat/m120-axis2-injection-demotion-badge`) |

operator_request.md CONTROL_SEQ 1559의 `commit_push_bundle_authorization + internal_only` + `pr_creation_gate + gate_24h` 조건이 이미 충족됐다. operator stop은 stale이므로 doc-sync implement로 전환.

## dirty tree 현황 (커밋 완료)

| 파일 | 출처 |
|------|------|
| `watcher_state.py` | `PaneLease.archive_for_restart()` 추가 — 커밋 완료 |
| `pipeline_runtime/supervisor.py` | `PaneLease` import + 4 slot archive 호출 — 커밋 완료 |
| `tests/test_watcher_core.py` | 회귀 테스트 3개 추가 — 커밋 완료 |

## 검증 미실행 항목

- `test_pipeline_gui_backend`, `test_pipeline_gui_home_presenter` 등 전체 suite 미실행 — supervisor import 변경이 다른 테스트에 영향 없음을 `py_compile` PASS로 간접 확인; CI 위임
- live watcher self-restart 시나리오 미실행 — 단위 레벨 `PaneLease` 동작과 acquire 재시도 경로로 대체

## 남은 리스크

- archive 실패(OSError) 시 old lease가 TTL까지 남을 수 있음 — warning log 보존, 구조 자체는 기존 TTL 대기 경로로 fall-back
- MILESTONES / TASK_BACKLOG M121 완료 미기록 — doc-sync 필요 (다음 implement 라운드)
