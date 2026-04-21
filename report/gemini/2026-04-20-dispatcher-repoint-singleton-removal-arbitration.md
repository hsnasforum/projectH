# 2026-04-20 dispatcher-repoint-singleton-removal-arbitration

## 상황 요약
- 5회 연속(seq 517→521) dispatcher-repoint 패턴이 관찰되었습니다.
- (a) **VERIFY lock-in**: `verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md` 파일이 서로 다른 `/work`들에 대해 4회 연속 context로 재주입됨.
- (b) **WORK reverse-walk**: 4/18 `/work` 파일들이 시간 역순(17:12 → 17:04 → 16:58 → 16:42)으로 디스패치됨.
- Seq 521 `operator_request`는 이를 "validated-bug"로 승격하고 `FIX_DISPATCHER_REPOINT`를 위한 owner component 및 defect-vector 지정을 요청했습니다.

## 분석 및 판단
- **원인 분석**: `pipeline_runtime.schema:latest_verify_note_for_work` 내의 "singleton fallback" 로직이 핵심 원인입니다.
  - 해당 로직은 특정 날짜 폴더에 `verify` 파일이 단 1개만 있고 그 파일에 명시적인 `work` 참조가 없을 경우, 해당 날짜의 모든 `work` 파일에 대해 그 파일을 "matching verify"로 간주합니다.
  - 이로 인해 `manual-cleanup`과 같은 특수 목적의 단일 파일이 해당 날짜의 모든 backlog work에 잘못 매핑되어 잘못된 context를 제공(lock-in)하게 됩니다.
  - 또한, `_work_has_matching_verify`의 mtime 체크가 이 singleton 파일에 대해 수행될 때, 파일이 과거 시점(`17:00`)에 고정되어 있다면 그 이후의 `work`들(`17:12`)은 "unverified"로 판정되어 디스패치 대상이 되고, 그 이전의 `work`들(`16:58` 등)은 순차적으로 "unverified" 후보가 되어 역순 진행(reverse-walk)을 유발합니다.
- **결정**: `pipeline_runtime.schema`를 책임 컴포넌트로 지정하고, singleton fallback 로직을 제거하는 `G7-dispatcher-repoint-singleton-removal` 슬라이스를 최우선 권고합니다.

## 권고 사항 (G7-dispatcher-repoint-singleton-removal)
- **RECOMMEND**: implement `G7-dispatcher-repoint-singleton-removal`
- **컴포넌트**: `pipeline_runtime.schema`
- **수정 위치**: `pipeline_runtime/schema.py:latest_verify_note_for_work` (약 L318-322)
- **변경 내용**: `if candidate_count == 1 and not latest_any_refs:` 블록을 제거하거나 비활성화하여, 명시적인 참조(`BASED_ON_WORK` 등)가 없는 singleton 파일이 임의의 `work`를 "대표"하지 못하도록 차단합니다.
- **기대 효과**: 잘못된 context 주입(lock-in)을 즉시 중단하고, backlog crawl 시 misleading context 없이 "honest state"에서 triage를 수행하게 함으로써 dispatcher 정합성을 회복합니다.

## 기타 후보 검토
- **G7-gate-blocking**: 현재 dispatcher repoint 버그가 파이프라인 정합성을 해치고 있으므로, gate 정책 강화보다 버그 수정이 선행되어야 합니다.
- **G11/G8/G3**: internal logic drift가 확인된 시점이므로 broader audit보다 명확한 defect 수정을 우선합니다.
