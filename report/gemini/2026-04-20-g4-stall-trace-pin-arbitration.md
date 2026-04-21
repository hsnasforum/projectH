# 2026-04-20 AXIS-G4 Stall Trace Pin Arbitration

## 조언 요약
- **결정**: 차기 구현 슬라이스로 **AXIS-G4 (stall-trace pin)**를 추천합니다.
- **선택 이유**: 현재 런타임(`.pipeline/runs/20260420T142213Z-p817639/`)에서 supervisor는 레인을 `WORKING` 상태로 전환했으나, 실제 wrapper/lane 레벨에서는 작업 시작(requisition) 없이 `HEARTBEAT`만 반복되는 'Supervisor-to-Wrapper 신호 미스매치' 정체 현상이 관찰되었습니다. 이는 시스템의 신뢰성과 직결된 리스크이므로, baseline을 넘기는 AXIS-G6(테스트 수정)보다 우선순위가 높습니다.
- **핀 세부 사항**:
    1. **Stall Family**: Supervisor-to-Wrapper dispatch signal mismatch (WORKING 상태 전이 후 태스크 수신 부재).
    2. **증거 구간**: `events.jsonl` seq 233~423 구간 (Claude WORKING 주기이나 영수증/결과물 없음).
    3. **구현 범위**: `work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall.md` 기록 및 `tests/test_watcher_core.py` 내 `WatcherDispatchQueue` 관련 테스트 골격(skeleton) 작성.

## 후보 비교 및 검토
- **(A) AXIS-G4**: 런타임 정체 현상의 구체적인 증거(seq 233-423)가 확보되었으며, 이를 추적하기 위한 전용 노트와 테스트 골격을 만드는 것은 향후 재귀 개선의 핵심 토대가 됩니다.
- **(B) AXIS-G6**: 10개의 `LocalOnlyHTTPServer` PermissionError 중 하나를 해결하는 작업이나, 1.4MB에 달하는 `tests/test_web_app.py`를 건드려야 하며 shared helper 확산 리스크가 있어 현재 단계에서는 후순위로 밀립니다.
- **기타**: Docs-only 슬라이스는 오늘 이미 2회 수행되어 saturation 임계치에 도달했으므로 제외합니다.

## 조치 권고 (RECOMMEND)
- `RECOMMEND: implement AXIS-G4 stall-trace pin`
- `TARGET_STALL: Supervisor-to-Wrapper signal mismatch`
- `EVIDENCE: run 20260420T142213Z-p817639, events.jsonl seq 233-423`
- `TEST_SKELETON: tests/test_watcher_core.py`
