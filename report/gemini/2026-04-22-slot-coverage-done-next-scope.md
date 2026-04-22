# 2026-04-22 slot coverage done next scope

## 개요
CONTROL_SEQ 756(Milestone 4 `trusted_source_count` 내부 필드 추가)이 완료됨에 따라, (1) 미커밋 작업의 커밋 타이밍, (2) 다음 Milestone 4 UI 노출 슬라이스 범위, (3) Milestone 6 `richer_reason_labels` 보류 적정성을 판단합니다.

## 중재 결과

### Q1 — Commit/push timing
**RECOMMEND: commit_push_now**
CONTROL_SEQ 756의 변경 사항(`core/web_claims.py`, `tests/test_smoke.py`, work/verify notes)은 로직과 테스트가 완비된 자기 완결적(self-contained)인 슬라이스입니다. 앞서 4축 워처/파이프라인 구조 개선(742–753)이 이미 큰 번들로 커밋(`3142b8e`)된 상태이므로, 개별 기능 단위인 756을 지금 커밋하여 `feat/watcher-turn-state` 브랜치의 미커밋 작업 누적 리스크를 줄이는 것이 적절합니다.

### Q2 — Next Milestone 4 slice
**RECOMMEND: `trusted_source_count` UI exposure**
내부적으로 확보된 `trusted_source_count`를 사용하여 "신뢰할 수 있는 단일 출처(weak)"와 "비신뢰 출처만 있는 소음(noise)"을 UI에서 구분하는 작업이 최우선입니다. 이는 Milestone 4의 "strong/weak/unresolved slots 분리 강화" 목표와 정확히 일치합니다.
- **Entry Points:**
    - `core/agent_loop.py` (lines 4291–4310): `coverage_items` 딕셔너리에 `trusted_source_count` 추가
    - `app/serializers.py` (lines 1001–1030): `_serialize_claim_coverage`에 필드 매핑 추가
    - `app/frontend/src/types.ts` (lines 60–65): `ClaimCoverageItem` 타입 업데이트
    - `app/frontend/src/components/MessageBubble.tsx` (lines 310–330): 배지 텍스트나 툴팁 등에 신뢰 출처 수 반영

### Q3 — richer_reason_labels deferral confirmation
**RECOMMEND: deferral confirmed**
Milestone 5 memory foundation(`39632a4`)이 최소한의 라벨(minimum labels) 지지 구조를 마련했으나, `TASK_BACKLOG.md` 275행의 제약("진실된 사용자 입력 인터페이스가 존재할 때만 확장")은 여전히 유효합니다. 현재 Phase의 집중 과제인 Milestone 4(Investigation Hardening)를 완결하고, 실제 사용자 피드백 루프가 더 성숙해지는 시점으로 Milestone 6 확장을 미루는 756 핸드오프의 판단이 옳습니다.

## 권고 요약
1. 현재의 756 작업을 커밋 및 푸시합니다.
2. 다음 슬라이스로 `trusted_source_count`를 UI(배지 또는 라벨)에 노출하여 정보 품질의 차이를 시각화합니다.
3. Milestone 6 `richer_reason_labels`는 Milestone 4 완료 이후로 보류를 유지합니다.
