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

---

## CONTROL_SEQ 756 구현 검증 (NEXT_CONTROL_SEQ: 757)

### 검증 대상 work note

`work/4/22/2026-04-22-slot-coverage-trusted-count.md`

### 검증 결과

- `core/web_claims.py:30` `SlotCoverage.trusted_source_count: int = 0` 필드 존재 ✅
- `core/web_claims.py:133` `_trusted_supporting_source_count(record)` helper 존재 ✅
- `core/web_claims.py:193` `trusted_count = _trusted_supporting_source_count(primary)` 단일 호출 — 로직 중복 없음 ✅
- `core/web_claims.py:189` MISSING 슬롯 `trusted_source_count=0` ✅
- `core/web_claims.py:211` non-MISSING 슬롯 `trusted_source_count=trusted_count` ✅
- `tests/test_smoke.py:2674,2676` 비신뢰 출처만 있는 weak slot → `trusted_source_count=0` 검사 ✅
- `tests/test_smoke.py:2696` 공식 단일 출처 weak slot → `trusted_source_count >= 1` 검사 ✅
- `tests/test_smoke.py:2718` strong slot → `trusted_source_count >= 2` 회귀 검사 ✅
- `python3 -m py_compile core/web_claims.py core/contracts.py` → **통과** ✅
- `python3 -m unittest tests.test_smoke` → **144 tests OK** ✅
- UI / approval flow / 저장 스키마 / pipeline control 변경 없음 ✅
- `git status`: `M core/web_claims.py`, `M tests/test_smoke.py`, `?? work/4/22/2026-04-22-slot-coverage-trusted-count.md` — 미커밋 상태

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `trusted_source_count` 필드가 `SlotCoverage`에 additive하게 추가됐고,
`summarize_slot_coverage()`가 `_trusted_supporting_source_count()` 기존 helper를 재사용해
MISSING / non-MISSING 분기 모두에서 올바르게 채움. 3개 신규 회귀 테스트 모두 실제 line에 존재
하며 144 tests 통과. 새 `CoverageStatus` 값이나 UI/저장 변경 없음.

### 남은 리스크 (CONTROL_SEQ 756 이후)

- `trusted_source_count`는 현재 `SlotCoverage` 내부 필드만. 브라우저 claim-coverage payload나
  표시 문구로의 노출은 별도 슬라이스.
- CONTROL_SEQ 756 변경(core/web_claims.py, tests/test_smoke.py, work note)은 미커밋 상태.
  commit/push 타이밍 판단 필요.
- advisory seq 755가 권고한 `richer_reason_labels`는 TASK_BACKLOG.md 제약으로 CONTROL_SEQ 756
  handoff에서 명시적으로 defer됨. 이 deferral을 advisory가 확인해야 함.
- Milestone 4 "better separation" 항목에서 내부 필드 분리(DONE) 이후 display-layer 노출 slice
  scoping이 명확하지 않음.

### 다음 control

CONTROL_SEQ 757 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: (1) CONTROL_SEQ 756 미커밋 작업의 commit/push 타이밍, (2) 내부 `trusted_source_count`
  필드를 claim-coverage API/display에 노출하는 다음 슬라이스 scope, (3) advisory seq 755가
  권고한 `richer_reason_labels`의 deferral 확인 — 세 가지 모두 advisory 판단이 필요.

---

## CONTROL_SEQ 759 구현 검증 (NEXT_CONTROL_SEQ: 760)

### 검증 대상 work note

`work/4/22/2026-04-22-claim-coverage-trusted-count-exposure.md`

### 검증 결과

- `core/agent_loop.py:4255` MISSING 슬롯 `"trusted_source_count": 0` ✅
- `core/agent_loop.py:4304` non-MISSING 슬롯 `"trusted_source_count": int(getattr(slot_coverage, "trusted_source_count", 0) or 0)` ✅
- `app/serializers.py:1027` `_serialize_claim_coverage()` `"trusted_source_count": int(item.get("trusted_source_count") or 0)` ✅
- `app/frontend/src/types.ts:66` `ClaimCoverageItem` 인터페이스에 `trusted_source_count?: number` 추가 ✅
- `app/frontend/src/components/MessageBubble.tsx:314` `isTrustedWeak = item.status === "weak" && (item.trusted_source_count ?? 0) > 0` — WEAK badge amber/stone 분기 ✅
- `tests/test_smoke.py` lines 1345,1352,1359,1366,1382,1386,1389,1392,1395,1398,1420,1427,1434,1454-1457: `trusted_source_count` 전달 및 serializer 회귀 검사 ✅
- `docs/PRODUCT_SPEC.md:267` slot object shape에 `trusted_source_count` 설명 추가 ✅
- `docs/ARCHITECTURE.md:220` slot object shape에 `trusted_source_count` 설명 추가 ✅
- `python3 -m py_compile core/agent_loop.py app/serializers.py` → **통과** ✅
- `python3 -m unittest tests.test_smoke` → **144 tests OK** ✅
- `git diff --check` → **통과** ✅
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage" --reporter=line` → **환경 차단** (sandbox socket permission 오류) — 코드 오류 아님, 소켓 허용 환경 재실행 필요 ⚠
- `npx tsc --noEmit` → **기존 오류 존재** (Sidebar.tsx SVG prop, useChat.ts applied_preferences 타입, main.tsx index.css declaration) — 이번 변경과 무관, `trusted_source_count` 타입 오류 없음 ⚠

### work note 클레임 진실성 평가

모든 클레임 **truthful**. pipeline 4단계(agent_loop → serializers → types.ts → MessageBubble.tsx)
가 모두 `trusted_source_count` 를 정확히 전달. badge 로직이 `isTrustedWeak` 변수로 amber/stone
분기 구현. serializer 회귀 테스트가 실제 line에 존재하며 144 tests 통과.
doc sync는 PRODUCT_SPEC과 ARCHITECTURE 두 파일에 동일 slot object shape 설명 추가.
Playwright claim-coverage 슬라이스는 sandbox 소켓 권한 문제로 환경 차단 — 코드 오류가 아닌
실행 환경 제약.

### 남은 리스크 (CONTROL_SEQ 759 이후)

- CONTROL_SEQ 756+759 변경(core/web_claims.py, core/agent_loop.py, app/serializers.py,
  app/frontend/src/types.ts, MessageBubble.tsx, tests/test_smoke.py, docs/*)이 모두 미커밋.
  advisory seq 758이 `commit_push_now`를 권고했으나 아직 실행되지 않음.
- Playwright claim-coverage 슬라이스가 sandbox에서 소켓 권한 오류로 미실행. WEAK badge 렌더링
  변경(untrusted-only → stone "–")에 대한 browser-visible 검증이 환경 허용 시 필요.
- frontend TypeScript 기존 오류(Sidebar.tsx, useChat.ts, main.tsx)는 이번 변경과 무관하지만
  전체 tsc 검사가 실패 중. 별도 정리 필요.
- Milestone 4 "better separation" 항목은 내부 필드(seq 756)와 display 노출(seq 759) 모두 완료.
  나머지 Milestone 4 sub-item(source role labeling, multi-source weighting, reinvestigation)
  의 다음 구현 슬라이스가 advisory로 scope되지 않음.

### 다음 control

CONTROL_SEQ 760 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: (1) advisory seq 758의 `commit_push_now`가 seq 756+759 bundle 양쪽 미커밋 상태에서
  아직 미실행 — commit 범위 확정 필요, (2) Playground claim-coverage 슬라이스 환경 차단이
  다음 슬라이스 진행을 gate해야 하는지 판단 필요, (3) Milestone 4 나머지 sub-item의 다음
  구현 entry point가 현재 verify 범위에서 자명하지 않음.

---

## CONTROL_SEQ 762 구현 검증 (NEXT_CONTROL_SEQ: 763)

### 검증 대상 work note

`work/4/22/2026-04-22-second-pass-trusted-priority.md`

### 검증 결과

- `core/agent_loop.py:3805` `_pending_slot_sort_key()` 내부 helper 추출 존재 ✅
- `core/agent_loop.py:3808` tier 0: `CONFLICT` ✅
- `core/agent_loop.py:3810-3813` tier 1: non-MISSING + `getattr(slot_coverage, "trusted_source_count", 0) == 0` ✅
- `core/agent_loop.py:3814-3815` tier 2: MISSING + `prior_probe_count >= 1` ✅
- `core/agent_loop.py:3816-3817` tier 3: MISSING (첫 조사) ✅
- `core/agent_loop.py:3818-3819` tier 4: non-MISSING + already probed ✅
- `core/agent_loop.py:3820` tier 5: non-MISSING + not probed ✅
- `core/agent_loop.py:3825` `pending_slots.sort(key=_pending_slot_sort_key)` ✅
- backward compatibility: `getattr(slot_coverage, "trusted_source_count", 0)` 사용 ✅
- `tests/test_smoke.py:2594` `test_second_pass_prioritizes_conflict_slot_over_weak_slot` ✅
- `tests/test_smoke.py:2668` `test_second_pass_prioritizes_zero_trusted_weak_over_positive_trusted_weak` ✅
- `python3 -m py_compile core/agent_loop.py` → **통과** ✅
- `python3 -m unittest tests.test_smoke` → **146 tests OK** ✅ (신규 2개 포함)
- `git diff --check` → **통과** ✅
- UI / serializer / 저장 스키마 / pipeline control 변경 없음 ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `_pending_slot_sort_key()` helper가 `pending_slots.sort()` inline lambda를
대체해 6-tier 우선순위를 명시함. CONFLICT tier 0, untrusted-only(trusted_source_count==0) tier 1,
기존 MISSING 내부 순서(re-probed > new) tiers 2-3 보존, positive-trusted non-MISSING tiers 4-5.
신규 회귀 테스트 2개 실제 line에 존재하며 146 tests 통과.

### 남은 리스크 (CONTROL_SEQ 762 이후)

- seqs 756+759+762 변경이 모두 미커밋 상태. advisory seq 761이 `commit_push_now_bundle`(756+759)을
  권고했으나 seq 762까지 포함한 전체 bundle은 아직 commit되지 않음.
- Milestone 4 "reinvestigate weak or unresolved slots more effectively" ✅ DONE (seq 762).
  나머지 Milestone 4 sub-item(source role labeling, multi-source weighting) entry point 미scope.
- dirty tree에 이전 `/work`, `/verify`, `report/gemini` 파일과 frontend 변경이 함께 남아 있음.

### 다음 control

CONTROL_SEQ 763 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: (1) seq 762 추가로 커밋 대상 bundle이 확장 — commit 범위 재확정 필요,
  (2) 남은 Milestone 4 sub-item(source role labeling, multi-source weighting)의 다음 entry
  point가 현재 verify 범위에서 자명하지 않음.

---

## CONTROL_SEQ 765 구현 검증 (NEXT_CONTROL_SEQ: 766)

### 검증 대상 work note

`work/4/22/2026-04-22-claim-sort-trusted-tier.md`

### 검증 결과

- `core/web_claims.py:62` `_claim_sort_key()` 반환 타입 7-tuple로 변경 ✅
- `core/web_claims.py:63` `trusted_tier = 1 if record.source_role in TRUSTED_CLAIM_SOURCE_ROLES else 0` ✅
- `core/web_claims.py:65` `trusted_tier`가 반환 tuple의 첫 번째 원소 ✅
- `core/web_claims.py:114` `max([existing, current], key=_claim_sort_key)` — call site 변경 없음 ✅
- `core/web_claims.py:194` `max(items, key=_claim_sort_key)` — call site 변경 없음 ✅
- `TRUSTED_CLAIM_SOURCE_ROLES` 재정의/재임포트 없이 기존 module-level 상수 재사용 ✅
- `tests/test_smoke.py:2967` `test_claim_sort_key_trusted_source_beats_high_volume_untrusted` ✅
- `tests/test_smoke.py:2991` `test_claim_sort_key_higher_support_wins_within_trusted_tier` ✅
- `python3 -m py_compile core/web_claims.py core/contracts.py` → **통과** ✅
- `python3 -m unittest tests.test_smoke` → **148 tests OK** ✅ (신규 2개 포함)
- `git diff --check` → **통과** ✅
- UI / serializer / 저장 스키마 / pipeline control 변경 없음 ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `_claim_sort_key()` 7-tuple 확장 확인. `trusted_tier` 첫 기준으로
trusted source(OFFICIAL/WIKI/DATABASE/DESCRIPTIVE)가 untrusted(COMMUNITY/BLOG/PORTAL) volume보다
우선. 같은 trusted tier 내부에서 `support_count` 우선순위 유지. 신규 테스트 2개 실제 line에 존재.
148 tests 통과.

### 남은 리스크 (CONTROL_SEQ 765 이후)

- seqs 756+759+762+765 변경 모두 미커밋. advisory가 756+759+762 bundle commit을 권고했으나
  seq 765까지 포함한 bundle은 commit되지 않음.
- Milestone 4 "stronger official/news/wiki/community weighting" ✅ DONE (seq 765).
  나머지 Milestone 4 항목 "source role labeling"의 정확한 scope/entry point 미확정.
- frontend TypeScript 기존 오류(Sidebar.tsx, useChat.ts, main.tsx)는 이번 변경과 무관.

### 다음 control

CONTROL_SEQ 766 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: (1) seq 765 추가로 commit bundle이 더 확장 — 전체 Milestone 4 bundle(seqs 756-765)
  commit 타이밍 재확정 필요, (2) 남은 Milestone 4 "source role labeling" 항목의 정확한
  entry point가 현재 verify 범위에서 자명하지 않음, (3) Milestone 4 완료 여부 advisory 판단 필요.

---

## CONTROL_SEQ 768 구현 검증 (NEXT_CONTROL_SEQ: 769)

### 검증 대상 work note

`work/4/22/2026-04-22-entity-claim-sort-trusted-tier.md`

### 검증 결과

- `core/agent_loop.py:4142` `_entity_claim_sort_key()` 반환 타입 7-tuple ✅
- `core/agent_loop.py:4143` `trusted_tier = 1 if claim.source_role in TRUSTED_CLAIM_SOURCE_ROLES else 0` ✅
- `core/agent_loop.py:4156` `trusted_tier` 첫 번째 원소 ✅
- `core/agent_loop.py:4186,4205` `max()` call site 2개 변경 없음 ✅
- inline `role_priority` dict 유지 (handoff 제약) ✅
- `tests/test_smoke.py:3015` `test_entity_claim_sort_key_trusted_beats_high_volume_untrusted` ✅
- `python3 -m py_compile core/agent_loop.py` → **통과** ✅
- `python3 -m unittest tests.test_smoke` → **149 tests OK** ✅ (신규 1개 포함)
- `git diff --check` → **통과** ✅
- UI / serializer / 저장 스키마 / pipeline control 변경 없음 ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `_entity_claim_sort_key()` 7-tuple 확장 확인. `trusted_tier` 첫 기준으로
entity-card primary claim 선택에서 OFFICIAL/WIKI/DATABASE/DESCRIPTIVE 단건 claim이
COMMUNITY/BLOG/PORTAL 다건 claim보다 우선. `max()` call site 2개 자동 혜택. 신규 테스트 1개 실제
line에 존재. 149 tests 통과.

이것으로 `core/web_claims.py:_claim_sort_key()` (seq 765)와 `core/agent_loop.py:_entity_claim_sort_key()`
(seq 768) 간의 trusted-tier 계약 drift가 해소됨.

### 남은 리스크 (CONTROL_SEQ 768 이후)

- seqs 756+759+762+765+768 변경 모두 미커밋. advisory seq 767이 "sort-key truth-sync 검증 후
  commit" 조건을 부여했으므로 seq 768 완료로 조건 충족.
- Milestone 4 "source role labeling" 항목이 advisory seq 767에서 remaining으로 명시됐으나
  정확한 entry point/scope 미확정.
- frontend TypeScript 기존 오류(Sidebar.tsx, useChat.ts, main.tsx) 이번 변경과 무관.

### 다음 control

CONTROL_SEQ 769 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: (1) advisory seq 767의 defer_commit_push 조건(sort-key truth-sync 검증)이 seq 768로
  충족 — commit/push bundle 범위 재확정 필요, (2) 남은 Milestone 4 "source role labeling"
  entry point가 자명하지 않음, (3) Milestone 4 최종 완료 여부 확인 필요.

---

## CONTROL_SEQ 771 구현 검증 (NEXT_CONTROL_SEQ: 772)

### 검증 대상 work note

`work/4/22/2026-04-22-claim-coverage-source-role-tooltip.md`

### 검증 결과

- `app/frontend/src/components/MessageBubble.tsx:318`
  `title={item.source_role ? item.source_role.charAt(0).toUpperCase() + item.source_role.slice(1) : undefined}` ✅
- `MessageBubble.tsx:314` `isTrustedWeak` 로직 변경 없음 ✅
- `MessageBubble.tsx:323-329` badge className 분기, status suffix 변경 없음 ✅
- `source_role` 없거나 빈 값이면 `title=undefined` — 기존 badge 동일 렌더링 ✅
- `tests/test_smoke.py:1459` `test_serialize_claim_coverage_includes_source_role` ✅
- `python3 -m py_compile app/serializers.py` → **통과** ✅
- `python3 -m unittest tests.test_smoke` → **150 tests OK** ✅ (신규 1개 포함)
- `git diff --check` → **통과** ✅
- `app/serializers.py`, `app/frontend/src/types.ts`, `core/`, pipeline control 변경 없음 ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `MessageBubble.tsx:318`에 `title` tooltip이 추가됐고, `source_role`이
없거나 빈 값일 때 `undefined`로 graceful degradation. 기존 `isTrustedWeak` 판단, badge className,
status suffix("✓"/"?"/"–")는 변경 없음. 신규 serializer 회귀 테스트 1개 실제 line에 존재.
150 tests 통과.

advisory seq 770이 "이 슬라이스로 Milestone 4 완전 종료" 확인 → Milestone 4 fully closed.

### 남은 리스크 (CONTROL_SEQ 771 이후)

- seqs 756+759+762+765+768+771 변경 모두 미커밋. advisory seq 770이 seqs 756-768 commit을
  권고했고, seq 771까지 포함한 전체 bundle이 대기 중.
- Milestone 4 "Secondary-Mode Investigation Hardening" ✅ 완료 (seqs 756+759+762+765+768+771).
- 다음 Milestone 5 첫 entry slice scope 미확정.
- frontend TypeScript 기존 오류(Sidebar.tsx, useChat.ts, main.tsx) 이번 변경과 무관.

### 다음 control

CONTROL_SEQ 772 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: (1) Milestone 4 완료 — commit/push bundle(seqs 756-771) 최종 확정 필요,
  (2) Milestone 5 첫 entry slice가 advisory 없이 자명하지 않음.

---

## CONTROL_SEQ 774 구현 검증 (NEXT_CONTROL_SEQ: 775)

### 검증 대상 work note

`work/4/22/2026-04-22-content-reject-note-surface.md`

### 검증 결과

- `app/frontend/src/api/client.ts:112` `postContentVerdict()` — `POST /api/content-verdict`, payload `{session_id, message_id, content_verdict}` ✅
- `app/frontend/src/api/client.ts:129` `postContentReasonNote()` — `POST /api/content-reason-note`, payload `{session_id, message_id, reason_note}` ✅
- `app/frontend/src/types.ts:30` `content_verdict?: string` on `Message` ✅
- `app/frontend/src/types.ts:31` `content_reason_record?: ContentReasonRecord` on `Message` ✅
- `app/frontend/src/types.ts:71` `ContentReasonRecord` interface (`reason_scope`, `reason_label`, `reason_note?`, `recorded_at`, `artifact_id`, `source_message_id`) ✅
- `app/frontend/src/components/MessageBubble.tsx:44-45` `onContentVerdict?`, `onContentReasonNote?` props 추가 ✅
- `app/frontend/src/components/MessageBubble.tsx:261` `onContentVerdict && !rejected && !message.content_verdict` guard ✅
- `app/frontend/src/components/MessageBubble.tsx:295-297` reject 버튼 클릭 시 `onContentVerdict()` 호출, non-empty note면 `onContentReasonNote()` 호출 ✅
- `app/frontend/src/components/MessageBubble.tsx:311` "거절됨" indicator (`rejected` state 또는 `message.content_verdict === "rejected"`) ✅
- label dropdown, multi-select, multi-verdict 추가 없음 — plain textarea only ✅
- `python3 -m unittest tests.test_smoke` → **150 tests OK** (이번 변경으로 신규 test 없음) ✅
- `git diff --check` → **통과** ✅
- `app/serializers.py`, `core/`, `storage/`, pipeline control 파일 변경 없음 ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. API helpers, types, MessageBubble props/state/UI 모두 code에서 확인됨.
150 tests 통과. MILESTONES.md Milestone 5 "still later" 제약 준수 — narrow surface만 추가.

**핵심 미완: parent call site 미연결.**
`ChatArea.tsx:120` `<MessageBubble>` 렌더에 `onContentVerdict`/`onContentReasonNote`가 전달되지
않음. `App.tsx`에도 핸들러 없음. 결과적으로 "내용 거절" 버튼은 현재 어떤 경로에서도 렌더되지 않음
(`onContentVerdict` prop이 `undefined`이면 UI 숨김).

### 남은 리스크 (CONTROL_SEQ 774 이후)

- seqs 756+759+762+765+768+771+774 변경 모두 미커밋. commit/push bundle 미실행.
- `ChatArea.tsx` + `App.tsx` parent wire-up 없으면 seq 774 content reject UI는 사실상 미동작.
- TypeScript 기존 오류(Sidebar.tsx, useChat.ts, main.tsx) 이번 변경과 무관, 미수정.

### 다음 control

CONTROL_SEQ 775 → `.pipeline/implement_handoff.md` (STATUS: implement)
- 이유: seq 774 content reject UI를 실동작하게 만드는 parent wire-up(ChatArea.tsx + App.tsx)이
  명확한 다음 slice. advisory 없이 자명하고 안전 범위 내.

---

## CONTROL_SEQ 775 구현 검증 (NEXT_CONTROL_SEQ: 776)

### 검증 대상 work note

`work/4/22/2026-04-22-content-reject-parent-wire-up.md`

### 검증 결과

- `app/frontend/src/components/ChatArea.tsx:29-30` `onContentVerdict?`, `onContentReasonNote?` props interface 추가 ✅
- `app/frontend/src/components/ChatArea.tsx:50-51` destructure 추가 ✅
- `app/frontend/src/components/ChatArea.tsx:129-130` `messages.map()` `<MessageBubble>`에 두 prop 전달 ✅
- streaming bubble(line 134+)에는 전달 없음 — handoff 제약 준수 ✅
- `app/frontend/src/App.tsx:7` `postContentVerdict`, `postContentReasonNote` import 추가 ✅
- `app/frontend/src/App.tsx:47-54` `handleContentVerdict` — `postContentVerdict` 호출, `chat.loadSession` reload, error toast ✅
- `app/frontend/src/App.tsx:56-62` `handleContentReasonNote` — `postContentReasonNote` 호출, error toast ✅
- `app/frontend/src/App.tsx:133-134` `<ChatArea>`에 두 핸들러 전달 ✅
- `MessageBubble.tsx`, `api/client.ts`, `types.ts`, backend, docs 변경 없음 ✅
- `python3 -m unittest tests.test_smoke` → **150 tests OK** ✅
- `git diff --check -- app/frontend/src/components/ChatArea.tsx app/frontend/src/App.tsx` → **통과** ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. `App → ChatArea → MessageBubble` 전체 prop chain 완성.
"내용 거절" 버튼이 이제 실제 backend(`POST /api/content-verdict`, `POST /api/content-reason-note`)를
호출할 수 있는 경로가 닫혔음. streaming bubble 미전달 확인.

**Milestone 5 "still later" 완전 종료:**
`docs/MILESTONES.md:198-200`의 "keep the first optional reject-note surface narrow and separate
from richer reject labels" 항목 = seqs 774(UI 추가) + 775(parent wire-up)로 완료.
나머지 "still later" 항목(`keep corrected-save bridge expansion narrow`)은 구현 항목이 아닌
constraint directive.

### 남은 리스크 (CONTROL_SEQ 775 이후)

- seqs 756+759+762+765+768+771+774+775 전체 미커밋.
- Milestone 4("Secondary-Mode Investigation Hardening", seqs 756-771) ✅ 완료.
- Milestone 5("Grounded Brief Contract", seqs 774-775 포함) ✅ 완료 추정.
- Milestone 6 첫 entry slice 미확정 — advisory 확인 필요.
- TypeScript 기존 오류(Sidebar.tsx, useChat.ts, main.tsx) 이번 변경과 무관.

### 다음 control

CONTROL_SEQ 776 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: (1) Milestone 5 "still later" content reject surface 완료로 Milestone 5 전체 종료 확정 필요,
  (2) commit/push bundle 범위가 756-771 → 756-775로 확대됐으므로 advisory 재확인 필요,
  (3) Milestone 6 첫 entry slice advisory 없이 자명하지 않음.
