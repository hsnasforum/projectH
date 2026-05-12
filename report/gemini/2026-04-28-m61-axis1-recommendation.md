# Advisory Log: 2026-04-28 — M61 Axis 1 방향 권고

## 개요
PR #51(M60 Axis 1+2) 머지 완료로 `main` 브랜치에 모든 TypedDict 계약(M54-M60)이 반영됨. 다음 마일스톤 M61의 첫 슬라이스 방향을 결정함.

## 분석
- **현 상태**: TypedDict 정규화가 완료되어 저장소 레이어의 안정성이 확보됨. `TASK_BACKLOG`의 다음 단계인 "physical correction analytics/validation"으로 진입하기 위한 기반이 마련됨.
- **리스크**: 복잡한 분석 로직을 한 번에 구현하기보다, 현재 누적된 교정(Correction) 데이터의 현황을 파악할 수 있는 최소한의 가시성(Visibility) 확보가 우선임.
- **기회**: `/api/corrections/summary` 엔드포인트를 통해 세션별 교정 빈도와 주요 교정 패턴을 요약 제공함으로써, "Reviewed-Memory" 루프의 실질적인 성능을 측정할 수 있는 지표를 마련할 수 있음.

## 권고 사항
`RECOMMEND: implement M61 Axis 1 — correction analytics summary`

### 구현 방향
1. **백엔드**: `AggregateHandlerMixin` (또는 신규 `AnalyticsHandlerMixin`)에 `get_correction_summary()` 메서드 추가.
2. **저장소 활용**: `CorrectionStore.scan_all()`을 통해 전체 교정 기록을 읽고, 세션별/패턴별(fingerprint) 통계 산출.
3. **API**: `GET /api/corrections/summary` 엔드포인트 노출 (`app/web.py` do_GET).
4. **검증**: `tests/test_correction_analytics.py` (신규) 또는 기존 handler 테스트에 통계 정확도 검증 케이스 추가.

### 우선순위 근거
- **Strategic Alignment**: `TASK_BACKLOG`의 "physical correction analytics" 첫 단추로서 가장 bounded되고 가시적인 성과임.
- **Structural Integrity**: TypedDict가 도입된 `CorrectionRecord`를 실제 대량 소비하는 첫 사례로서, 타입 안정성을 실전 검증할 수 있음.
- **Operational Value**: 운영자가 현재 시스템이 얼마나 많은 교정을 유도하고 있는지 정량적으로 파악할 수 있게 함.

## 결론
M61의 첫 슬라이스로 교정 통계 요약 엔드포인트 구현을 권장하며, 이는 향후 더 깊은 분석 및 검증 도구의 기초가 될 것임.
