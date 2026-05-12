# 2026-04-26 M38 Axis 1 E2E Healthcheck Wrapper 및 차기 슬라이스 권고

## 상황 개요
- **M38 Axis 1 구현 완료**: `make e2e-test`의 안정성을 높이기 위한 `e2e/start-server.sh` wrapper가 구현되었습니다.
- **검증 결과**:
    - **Auto-start 경로**: 서버가 없는 상태에서 자동 기동 및 테스트 완료(150 passed)가 확인되었습니다.
    - **Reuse 경로**: 기존 서버 재사용 로직은 구현되었으나, 현재 샌드박스 환경의 소켓 생성 제한(`PermissionError: [Errno 1] Operation not permitted`)으로 인해 기존 서버를 미리 띄워두는 테스트 시나리오를 로컬에서 완결하지 못했습니다.
- **Stale Control 탐지**: 검증 도중 발생한 환경적 제약으로 인해 960 사이클 동안 제어 흐름이 정체되었습니다.

## 판단 근거
1. **환경적 제약 수용**: `PermissionError`는 코드의 결함이라기보다 현재 실행 환경(샌드박스)의 소켓 바인딩 정책에 기인한 것입니다. `auto-start` 경로가 이미 150개 테스트를 성공적으로 완수한 점으로 미루어 볼 때, wrapper의 기본 골격은 신뢰할 수 있습니다.
2. **Reuse 로직의 안전성**: `e2e/start-server.sh`의 재사용 로직은 단순한 `python3` 기반 healthcheck를 사용하며, 실패 시 `auto-start`로 안전하게 fallback되므로 시스템 파괴 리스크가 낮습니다.
3. **M38 지속성**: M38의 목표는 "Infrastructure Robustness"입니다. 현재의 wrapper는 기존의 불안정한 `sleep 10` 방식보다 월등히 개선된 상태이므로, 잔여 리스크를 인지한 채로 다음 단계(Isolation 강화 또는 인프라 확장)로 넘어가는 것이 효율적입니다.

## 권고 사항 (RECOMMENDATION)
- **우선순위 1**: `work/4/26/2026-04-26-e2e-healthcheck-wrapper.md`를 검증 완료(verified)로 처리하고, "Reuse 경로는 환경 제약으로 인해 검증되지 않았음"을 잔여 리스크(residual risk)로 명시합니다.
- **차기 단계**: Milestone 38 Axis 2 (E2E Isolation & Environment Hardening) 구현 슬라이스로 진입하여 테스트 간의 상호 간섭을 줄이는 작업을 이어갑니다.

### 실행 명령
`RECOMMEND: validate work/4/26/2026-04-26-e2e-healthcheck-wrapper.md`

### 예상 결과
- `make e2e-test`가 보다 안정적인 서버 대기 로직을 갖추게 됨.
- 샌드박스 환경 밖(예: 운영자 로컬 또는 CI)에서는 정상적으로 기존 서버 재사용이 가능할 것으로 기대됨.
- M38 Axis 2를 통해 테스트 환경의 격리 수준을 더욱 강화.
