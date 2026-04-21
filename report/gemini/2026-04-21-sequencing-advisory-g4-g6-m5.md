# 2026-04-21 G4-G15 통합 및 Milestone 5 전환 가이던스

## 개요
CONTROL_SEQ 620 기반의 sequencing advisory 요청에 대해, G6 (PermissionError) 원인 분석 결과와 G4 E2E/Idle-release 검증 및 브랜치 마무리 우선순위를 제안합니다.

## 분석 결과

### 1. AXIS-G6 (PermissionError) 성격 규정
- **원인**: `LocalOnlyHTTPServer(("127.0.0.1", 0), ...)` bind 시 발생하는 `PermissionError: [Errno 1] Operation not permitted`는 샌드박스/환경의 소켓 시스템 콜 제한으로 인한 **EPERM**입니다.
- **재현**: 구현 환경(Implement owner)에서는 성공하나, 특정 제약이 걸린 검증 환경(Verify owner)에서만 10건의 에러가 발생합니다. 이는 코드 버그가 아닌 **환경적 요인**입니다.
- **권고**: 이를 우회하기 위한 복잡한 구현(Implement)보다는, **"샌드박스 환경의 루프백 바인드 제한으로 인한 알려진 실패"로 베이스라인에 기록**하고 AXIS-G6를 닫을 것을 권장합니다.

### 2. G4 E2E 및 Watcher Idle-release 검증
- **상태**: 두 항목 모두 코드상으로는 code-green(152/152 OK)이나, 런타임 프로세스(watcher)가 재시작되어야 실제 동작이 활성화됩니다.
- **권고**: 현재의 dirty worktree 상태에서 런타임을 재시작하여 G4 `DISPATCH_SEEN` 방출 여부와 새롭게 추가된 `claude_handoff_idle_release` 경로를 실환경에서 최종 확인해야 합니다.

## 권장 실행 순서 (Sequencing Recommendation)

Gemini는 아래 순서로 라운드를 진행하여 `feat/watcher-turn-state` 브랜치를 안전하게 닫고 Milestone 5로 전환할 것을 권고합니다.

1. **[Verify] 런타임 재시작 및 실환경 검증**:
   - Watcher 재시작을 통해 idle-release 로직 활성화.
   - Implement lane이 busy할 때 handoff가 defer되는지, 이후 idle로 전환될 때 release되는지 확인.
   - G4 `ctrl-{seq}` task hint 필드가 실제 `DISPATCH_SEEN`으로 이어지는지 확인.
2. **[Handoff] G6 베이스라인 기록**:
   - `tests.test_web_app`의 10건 PermissionError를 환경 제약으로 명시하고 AXIS-G6 종료.
3. **[Operator/Handoff] 통합 커밋 및 푸시**:
   - G4~G15, metadata canonicalization, idle-release가 포함된 현재의 대규모 dirty worktree를 `feat/watcher-turn-state` 브랜치에 하나의 논리적 묶음으로 커밋.
4. **[Advisory/Next] Milestone 5 전환**:
   - 모든 검증이 완료된 시점에서 Milestone 5 (Grounded Brief Contract)로 축을 전환.

## 결론
현재 구현된 모든 축(G4-G15)은 정합성이 확인되었으므로, 환경 이슈인 G6에 시간을 소모하지 말고 실환경 최종 검증 후 브랜치를 커밋/푸시하여 Milestone 5로 넘어가는 것이 가장 효율적입니다.
