# 2026-04-22 post-cleanup launcher automation realignment

## 변경 파일
- `verify/4/22/2026-04-22-post-cleanup-launcher-automation-realignment.md`
- `.pipeline/implement_handoff.md`

## 사용 skill
- `round-handoff`: 최신 `/work`, `/verify`, advisory advice를 다시 읽고 다음 실행 control을 pipeline automation 축으로 재정렬하기 위해 사용했습니다.

## 변경 이유
- 현재 active control은 `.pipeline/advisory_advice.md` CONTROL_SEQ 741이며, 권고 내용은 product milestone 재개가 아니라 `pipeline_runtime` shared state parsing입니다.
- 다만 `.pipeline/codex_feedback.md`에는 오래된 4월 3일 product/e2e slice가 남아 있고, `.pipeline/operator_request.md`에도 superseded publish/product context가 남아 있어 current 작업 방향이 milestone 쪽으로 보일 수 있습니다.
- 따라서 advisory advice를 더 높은 CONTROL_SEQ 742 `implement_handoff.md`로 수렴해 다음 round가 pipeline launcher / watcher / supervisor 자동화 안정화만 실행하도록 명확히 했습니다.

## 확인한 current truth
- `parse_control_slots(Path(".pipeline"))` 확인 전 active:
  - active: `.pipeline/advisory_advice.md`
  - status: `advice_ready`
  - CONTROL_SEQ: `741`
- `report/gemini/2026-04-22-post-cleanup-next-slice.md`는 product milestone을 보류하고 `shared state parsing`을 권고합니다.
- `work/4/22/2026-04-22-runtime-legacy-control-cleanup-closeout.md`는 CONTROL_SEQ 739 legacy naming cleanup이 runtime control slot 정리였음을 기록합니다.

## 다음 control
- `.pipeline/implement_handoff.md` CONTROL_SEQ 742로 `pipeline_launcher_shared_state_parsing` 실행 handoff를 작성했습니다.
- 다음 implement owner는 product milestone, reviewed-memory UI, browser smoke, `app/`, `core/`, `storage/` 쪽으로 넓히지 않고 `pipeline_runtime` / watcher / supervisor state parsing owner 경계만 다뤄야 합니다.
- `.pipeline/codex_feedback.md`는 stale legacy scratch로만 취급하며 실행 slot이 아닙니다.
- `.pipeline/operator_request.md` CONTROL_SEQ 734는 superseded publish context이므로 current next slice 근거가 아닙니다.

## 검증
- 문서/rolling control 재정렬만 수행했습니다.
- 코드 변경은 하지 않았으므로 unit/e2e는 재실행하지 않았습니다.
- `python3 -c "from pathlib import Path; from pipeline_runtime.schema import parse_control_slots; r=parse_control_slots(Path('.pipeline')); print('active:', r['active']['file'], r['active']['control_seq'])"`
  - 결과: `active: implement_handoff.md 742`
- `git diff --check -- .pipeline/implement_handoff.md verify/4/22/2026-04-22-post-cleanup-launcher-automation-realignment.md`
  - 결과: 통과

## 남은 리스크
- GUI/backend control parser 중복은 Windows/WSL I/O adapter 계약 때문에 다음 구현자가 무리하게 통합하면 안 됩니다. 필요한 경우 runtime shared parser에 I/O adapter callback을 두는 방식으로 후속 처리하는 편이 안전합니다.
- stale `.pipeline/codex_feedback.md`와 `.pipeline/operator_request.md`는 여전히 root에 남아 있지만 current active control은 CONTROL_SEQ 742 `implement_handoff.md`입니다.

---

## CONTROL_SEQ 742 구현 검증 (NEXT_CONTROL_SEQ: 743)

### 검증 대상 work note

`work/4/22/2026-04-22-active-control-snapshot.md`

### 검증 결과

- `pipeline_runtime/schema.py:79` `ActiveControlSnapshot` TypedDict 존재 확인 ✅
- `pipeline_runtime/schema.py:624` `active_control_snapshot_from_entry()` 존재 확인 ✅
- `pipeline_runtime/schema.py:660` `active_control_snapshot_from_status()` 존재 확인 ✅
- `watcher_core.py` lines 92–93, 1992, 2004, 2053: 두 helper import + 3개 call site ✅
- `supervisor.py` lines 52–54, 498, 521, 538, 685–686, 780, 1169, 1301, 1378, 1609, 1696: 광범위 사용 ✅
- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py` → **통과** ✅
- `python3 -m unittest tests.test_pipeline_runtime_schema` → **42 tests OK** ✅
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_watcher_core` → **321 tests OK** ✅
- `git diff --check` → **통과** ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `ActiveControlSnapshot` TypedDict + 두 helper가 schema.py에 있고,
watcher와 supervisor 양쪽에서 사용 중. 기존 `active_control_*` JSON key 형상 유지.
테스트 카운트(42 schema, 321 supervisor+watcher)도 실제와 일치.

### 남은 리스크 (CONTROL_SEQ 742 이후)

- 4축 owner bundle 중 axis 1(shared state parsing) 완료. 나머지 3축(verify close chain /
  lease release / active_round selection) 미구현.
- GUI/backend parser 중독은 Windows/WSL adapter 계약 때문에 보수적으로 유지.
- `status.json` schema version bump 및 관련 doc 변경은 이번 범위 밖.

### 다음 control

CONTROL_SEQ 743 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: axis 2 (verify close chain)의 정확한 code boundary가 현재 handoff에서 scope되지
  않았고, 최신 advisory가 axis 1만 명시했으므로 axis 2 scoping을 위해 advisory-first 적용

---

## CONTROL_SEQ 745 기반 work note 검증 (NEXT_CONTROL_SEQ: 746)

### 검증 대상 work note

`work/4/22/2026-04-22-pipeline-control-shared-snapshot.md`

참고: 이 work note는 `CONTROL_SEQ 742 pipeline_launcher_shared_state_parsing`의 확장
구현을 완료한 것으로 기록됨. CONTROL_SEQ 745 (verify_close_chain) 핸드오프 context에서
verify하나, work note 자체의 변경 파일과 클레임만 기준으로 판단함.

### 검증 결과

- `pipeline_runtime/schema.py:88` `PipelineControlSnapshot` TypedDict 존재 확인 ✅
  - fields: `active: ActiveControlSnapshot`, `stale: list[ActiveControlSnapshot]`, `active_entry`, `stale_entries`, `slots`
- `pipeline_runtime/schema.py:701` `pipeline_control_snapshot_from_slots()` 존재 확인 ✅
- `pipeline_runtime/schema.py:728` `read_pipeline_control_snapshot()` 존재 확인 ✅
- `watcher_core.py:103, 2206` import + call site ✅
- `supervisor.py:65, 1694` import + call site ✅
- `pipeline_gui/backend.py` non-Windows branch 연결 (GUI test 통과로 간접 확인) ✅
- `python3 -m py_compile ... pipeline_gui/backend.py` → **통과** ✅
- `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_supervisor tests.test_watcher_core` → **365 tests OK** ✅
- `python3 -m unittest tests.test_pipeline_gui_backend` → **48 tests OK** ✅
- `git diff --check` → **통과** ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `PipelineControlSnapshot` + 두 helper가 schema.py에 있고,
watcher와 supervisor 양쪽에서 소비 중. GUI backend 48 테스트 통과. 기존 JSON key 형상 유지.

### 남은 리스크 (CONTROL_SEQ 745 이후)

- `verify_fsm.py`는 `PipelineControlSnapshot` / `read_pipeline_control_snapshot()` 미사용 확인:
  axis 2 (verify close chain) 구현이 아직 없음. CONTROL_SEQ 745 handoff 작성됐으나 미실행.
- CONTROL_SEQ 746에서 verify_close_chain을 `read_pipeline_control_snapshot()` 기반으로 재scope하여 handoff 작성 필요.
- Windows/WSL GUI backend subprocess parser는 여전히 분리 유지.

### 다음 control

CONTROL_SEQ 746 → `.pipeline/implement_handoff.md` (STATUS: implement)
- 이유: verify_close_chain (axis 2) 구현 방향 명확. `read_pipeline_control_snapshot()`이
  이미 존재하므로 추가 advisory 없이 직접 handoff 작성 가능. `verify_fsm.py` StateMachine이
  단일 owner bound이며 테스트 범위가 명확함.

---

## CONTROL_SEQ 747 구현 검증 (NEXT_CONTROL_SEQ: 748)

### 검증 대상 work note

`work/4/22/2026-04-22-verify-close-chain-snapshot.md`

### 검증 결과

- `verify_fsm.py:14,17` `PipelineControlSnapshot`, `read_pipeline_control_snapshot` import ✅
- `verify_fsm.py:232` `pipeline_dir: Optional[Path] = None` 파라미터 존재 ✅
- `verify_fsm.py:262` `self.pipeline_dir = pipeline_dir` 저장 ✅
- `verify_fsm.py:793,835,837` snapshot-first `control_changed` 분기 + fallback 유지 ✅
- `verify_fsm.py:796` dispatch 시 snapshot active seq → `job.dispatch_control_seq` 갱신 ✅
- `watcher_core.py:1691` `pipeline_dir=self.pipeline_dir` StateMachine 생성자 연결 ✅
- `supervisor.py:1608–1630` `_reconcile_receipts`에서 `active_control_snapshot_from_status()` 사용 + `receipt_written` event payload에 control 정보 포함 ✅
- `tests/test_verify_fsm.py` 존재 확인 ✅
- `python3 -m unittest tests.test_verify_fsm` → **3 tests OK** ✅
- `python3 -m py_compile verify_fsm.py pipeline_runtime/supervisor.py watcher_core.py pipeline_runtime/schema.py` → **통과** ✅
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_watcher_core` → **321 tests OK** ✅
- `git diff --check` → **통과** ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. 1차 실패(snapshot `-1`이 기존 `dispatch_control_seq`를 덮어써 4개
실패) → snapshot이 비어 있을 때 기존 seq 보존하도록 수정 → 최종 321 tests 통과. 이 흐름도
work note에 정확히 기록됨.

### 남은 리스크 (CONTROL_SEQ 747 이후)

- 4축 bundle 진행 상황:
  - axis 1 (shared state parsing) ✅ DONE
  - axis 2 (verify close chain) ✅ DONE
  - axis 3 (lease release) — 미구현, 정확한 code boundary 불명확
  - axis 4 (active_round selection) — 미구현
- `feedback_baseline_sig`, `verify_feedback_baseline_sig`, `compute_multi_file_sig()` fallback 유지
- Windows/WSL GUI backend subprocess parser 분리 유지

### 다음 control

CONTROL_SEQ 748 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: axis 3 (lease release)의 정확한 code boundary가 현재 codebase에서 자명하지 않음.
  advisory (seq 744)가 axis 2 안정화 후로 명시적으로 defer했으므로, axis 3 scoping을
  위해 advisory-first 적용

---

## CONTROL_SEQ 750 구현 검증 (NEXT_CONTROL_SEQ: 751)

### 검증 대상 work note

`work/4/22/2026-04-22-verify-lease-release-consolidation.md`

### 검증 결과

- `verify_fsm.py:278` `_release_verify_lease(slot, job=None, *, reason="")` helper 존재 ✅
- `verify_fsm.py:587,629,678,820,833,929,1038,1097` 8개 call site 모두 `_release_verify_lease()` 사용 ✅
- `verify_fsm.py:279` helper 내부의 `self.lease.release(slot)` 1개만 남음 (직접 호출 완전 제거) ✅
- `watcher_core.py:3439` `log.info("lease released: slot=slot_verify reason=archive_matching_verified_pending")` 추가 확인 ✅
- `python3 -m py_compile verify_fsm.py watcher_core.py` → **통과** ✅
- `python3 -m unittest tests.test_verify_fsm` → **5 tests OK** ✅
- `python3 -m unittest tests.test_watcher_core` → **191 tests OK** ✅
- `git diff --check` → **통과** ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. 8개 직접 호출 → helper 교체 완전 확인.
각 call site에 transition reason 부여됨. watcher_core.py 예외 호출은 helper 래핑 없이
log.info 추가로 관찰 가능하게 처리.

### 남은 리스크 (CONTROL_SEQ 750 이후)

- 4축 bundle 진행 상황:
  - axis 1 (shared state parsing) ✅ DONE
  - axis 2 (verify close chain) ✅ DONE
  - axis 3 (lease release) ✅ DONE
  - axis 4 (active_round selection) — 미구현, advisory (seq 749)가 lifecycle 안정화 후로 defer
- schema.py `ActiveControlSnapshot` lease-field 확장은 follow-up으로 명시적 defer 유지
- 오늘 쌓인 dirty/untracked 파일들은 구현 완료 bundle에서 정리 예정

### 다음 control

CONTROL_SEQ 751 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: axis 4 (active_round selection)의 정확한 code boundary가 불명확.
  advisory (seq 749)가 lifecycle 안정화 후로 defer했고 그 안정화가 확인됐으므로
  axis 4 scoping을 위해 advisory-first 적용

---

## CONTROL_SEQ 753 구현 검증 (NEXT_CONTROL_SEQ: 754)

### 검증 대상 work note

`work/4/22/2026-04-22-active-round-control-seq-selection.md`

### 검증 결과

- `supervisor.py:895` `_build_active_round` 시그니처에 `active_control` 파라미터 추가 ✅
- `supervisor.py:905–906` `active_control_snapshot_from_status()` → `active_control_seq` 도출 ✅
- `supervisor.py:932–935` `_control_seq_rank` inner 함수 — seq 일치 job에 rank 1 부여 ✅
- `supervisor.py:948` max() key에 `_control_seq_rank` 첫 번째로 삽입 ✅
- `supervisor.py:1739` preview call site `active_control=active_control_block` 전달 확인 ✅
- `turn_arbitration.py:11` `active_control_snapshot_from_status` import ✅
- `turn_arbitration.py:199` `active_control_snapshot_from_status(dict(control or {}))` 사용 ✅
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/turn_arbitration.py` → **통과** ✅
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration` → **142 tests OK** ✅
- `git diff --check` → **통과** ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `_control_seq_rank` inner fn으로 active control_seq 일치 job이
timestamp/liveness 정렬보다 먼저 선택됨. active_control 없을 때 기존 정렬 fallback 유지.
turn_arbitration.py raw dict access → snapshot helper 전환 확인.

### 4축 owner bundle 최종 상태

- axis 1 (shared state parsing) ✅ DONE — `PipelineControlSnapshot`, `read_pipeline_control_snapshot()`
- axis 2 (verify close chain) ✅ DONE — StateMachine snapshot-first control_seq 비교
- axis 3 (lease release) ✅ DONE — `_release_verify_lease()` helper, 8 call site 통합
- axis 4 (active_round selection) ✅ DONE — `_build_active_round` control_seq 우선 정렬

Advisory (seq 752): "Once Axis 4 is complete, the entire infrastructure cleanup bundle
is closed, clearing the path for Milestone 5/6 resume."

### 남은 리스크 (CONTROL_SEQ 753 이후)

- 오늘 쌓인 dirty/untracked 파일들(work notes, verify notes, report files, code changes)이
  feat/watcher-turn-state 브랜치에 미커밋 상태. bundle 완료 지점에서 commit/push 검토 필요.
- schema.py `ActiveControlSnapshot` lease-field 확장은 follow-up으로 defer 유지.
- Milestone 5/6 재개 슬라이스 선택이 필요.

### 다음 control

CONTROL_SEQ 754 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: 4축 bundle 완료 — advisory (seq 752)가 Milestone 5/6 재개 경로 확보 확인.
  (1) 오늘 쌓인 작업의 commit/push 타이밍, (2) Milestone 6 첫 entry slice 선택,
  두 가지 모두 advisory 판단이 필요하여 advisory-first 적용
