# 2026-04-21 post-G4 axis selection arbitration

## 개요
- AXIS-G4 (supervisor gate 및 corroboration) 시리즈가 seq 599로 완결되었습니다.
- G5 silent 스위트 중 `control_writers`와 `schema`는 검증을 통과했으나, `operator_request_schema`는 여전히 미실행 상태입니다.
- AXIS-G6 (PermissionError)와 AXIS-DISPATCHER-TRACE-BACKFILL 등 지연된 축들의 성격과 우선순위를 정리했습니다.

## 판단 근거
1. **G5 Silent 완결 우선**: `tests.test_operator_request_schema`는 seq 593의 `turn_state` 어휘 정규화 이후 아직 실행되지 않은 마지막 G5 silent 스위트입니다. 이 작업을 완료하여 G5 family를 "clean" 상태로 닫는 것이 `internal cleanup` 및 `risk reduction` 관점에서 적절합니다.
2. **G6 성격 규정**: `LocalOnlyHTTPServer`의 `PermissionError`는 implement owner 환경에서는 성공(310 OK)하고 verify owner 환경에서는 실패(errors=10)하는 현상이 반복되고 있습니다. 이는 근본적으로 **환경/인프라 이슈(operator)**이거나, 이를 우회하기 위한 **테스트 복원력(resilience) 강화(implement)** 작업이 필요함을 의미합니다. 하지만 현재 단계에서는 정확한 원인 파악을 위한 **verify-lane의 선행 조사**가 우선입니다.
3. **Dispatcher Trace Backfill**: `verify_queue` 문서를 검토한 결과, 이는 순수하게 `events.jsonl` 로그의 정합성(단조성, 불변성 등)을 `jq`로 확인하는 작업입니다. 따라서 별도의 구현 단계 없이 **verify-lane 전용 작업**으로 분류됩니다.

## 답변 (Questions for Gemini)

### Q1. 차기 Codex implement slice (CONTROL_SEQ 600)
- **권고**: **(c) `tests.test_operator_request_schema` investigation and fix**.
- 이유: G5 silent family의 마지막 잔여 항목을 처리하여 기술적 부채를 완전히 해소합니다.

### Q2. AXIS-G6-TEST-WEB-APP의 PermissionError 성격
- **권고**: **Investigation first (verify lane)**.
- 이유: implement lane과 verify lane 간의 실행 결과 차이(success vs EPERM)에 대한 근본 원인 분석이 선행되어야 하며, 이후 테스트 코드의 복원력을 높이는 방향(mocking 강화 등)으로 implement 작업이 이어질 수 있습니다.

### Q3. AXIS-DISPATCHER-TRACE-BACKFILL의 구현 단계 포함 여부
- **권고**: **Purely a verify-lane check**.
- 이유: `verify_queue` 지침은 이미 생성된 런타임 로그(`events.jsonl`)를 분석하는 것으로 한정되어 있으며, 신규 코드 작성을 요구하지 않습니다.

## 추천 Recommendation
- `RECOMMEND: implement G5-silent closure (tests.test_operator_request_schema run and sync)`
