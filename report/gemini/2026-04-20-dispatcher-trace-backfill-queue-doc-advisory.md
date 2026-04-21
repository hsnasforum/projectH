# 2026-04-20 dispatcher trace backfill queue doc advisory

## 조언 내용
- **RECOMMEND: implement AXIS-G5-DEGRADED-BASELINE**
- 최신 런(`.pipeline/runs/20260420T142213Z-p817639/`)의 `events.jsonl`에서 `dispatch_selection` 이벤트가 21건 발견되었습니다. Gemini 572/575가 요구한 트리거 조건(>= 2 events)이 이미 충족되었으므로, `verify owner`는 다음 라운드에서 큐에 쌓인 `docs/projectH_pipeline_runtime_docs/verify_queue/2026-04-20-dispatcher-trace-backfill.md` 지침을 즉시 실행할 수 있습니다.
- `implement owner`를 위한 다음 슬라이스로는 `AXIS-G5-DEGRADED-BASELINE`(docs-only)을 추천합니다. 이는 GUI 백엔드 베이스라인의 현재 상태(residual test failures 등)를 문서화하여 "truthful runtime surface"를 유지하는 안전한 후속 단계입니다.
- 이번 라운드가 선택되면 오늘(2026-04-20)의 docs-only 라운드 횟수는 1에서 2로 증가하며, 3회 임계값(saturation threshold) 이내로 안전하게 관리됩니다.

## 판단 근거
1. **Trigger Condition Met**: 외부 트리거 대기 중이던 `DISPATCHER-TRACE-BACKFILL`의 조건이 이미 런타임 로그에 기록됨을 확인했습니다. 따라서 `verify-lane`은 실행 준비가 완료되었습니다.
2. **Implement Slice Selection**: `AXIS-G4`는 여전히 추가 stall trace가 필요해 보이며, `AXIS-G6`는 환경 의존적인 `PermissionError` 해결 작업으로 리스크가 상대적으로 높습니다. `AXIS-G5-DEGRADED-BASELINE`은 기존 G5 패밀리의 완결성과 문서 정합성을 맞추는 데 가장 적합한 "same-family" 후속 작업입니다.
3. **Docs-only Budget**: 오늘 총 1회의 docs-only 라운드가 진행되었으므로, 추가로 1~2회 더 진행하는 것은 "bounded docs bundle" 규칙에 저촉되지 않습니다.

## 리스크 및 주의사항
- `DISPATCHER-TRACE-BACKFILL` 검증 실행 시, `verify owner`는 큐 문서에 명시된 5개 검증 항목(Monotonicity, Consistency, Sentinel, Stability, Autonomy invariants)을 최신 런(`20260420T142213Z-p817639`) 데이터에 대조해야 합니다.
- `AXIS-G5-DEGRADED-BASELINE` 구현 시, `tests.test_web_app`의 10건 `PermissionError`와 `tests.test_pipeline_gui_backend`의 최신 상태를 베이스라인으로 명확히 기록해야 합니다.
