# 2026-04-24 m30-axis2-proxy-cleanup-stale-recovery

## 결정: M30 Axis 2 (proxy cleanup) 실행 유지 및 sequence 갱신

### 근거
1. **Stale Control 해소**: 현재 `.pipeline/implement_handoff.md`가 `CONTROL_SEQ: 137`에 머물러 있으며, 이는 이전 `verify`와 sequence가 충돌하여 watcher가 stale로 감지한 상태입니다.
2. **논리적 다음 단계**: M30 Axis 1(stub removal)이 성공적으로 완료되었으나, 테스트 호환성을 위해 도입된 `_LegacyPatchableSharedCall` 프록시가 `watcher_core.py`에 새로운 복잡도를 도입했습니다. 이 프록시를 제거하고 테스트를 canonical `_shared_*` 이름으로 마이그레이션하는 Axis 2 작업은 Milestone 30의 "구조 분해" 목표에 필수적입니다.
3. **작업 타당성**: 120곳의 테스트 패치 타겟 교체는 단순 문자열 치환으로 위험도가 낮으며, 프록시 코드를 완전히 제거하여 `watcher_core.py`를 더 순수한 thin client로 만들 수 있습니다.

### 권고 Slice
- `.pipeline/implement_handoff.md CONTROL_SEQ 137`에 기술된 **M30 Axis 2 (proxy cleanup)** 작업을 그대로 승격하여 진행.
- Sequence 충돌을 방지하기 위해 다음 implement handoff는 새로운 sequence(예: 140)로 작성할 것을 권고.

### 제외된 대안
- **다른 Milestone 전환**: 현재 `watcher_core.py`에 프록시라는 "과도기적 부채"가 남아 있는 상태에서 다른 작업으로 전환하는 것은 리스크가 큽니다. 구조 정리를 완료하는 것이 우선입니다.
