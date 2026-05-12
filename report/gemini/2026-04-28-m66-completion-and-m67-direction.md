# Advisory Log: 2026-04-28 — M66 완료 및 M67 방향 권고

## 개요
M66 Axis 1+2 완료를 통해 교정 패턴 "무시(Dismiss)" 기능이 추가되었으며, JSON/SQLite 양쪽의 기술적 패리티가 확보됨. 다음 마일스톤 M67에서는 집계된 패턴(Aggregated Patterns)뿐만 아니라, 최근에 발생한 개별 교정 기록들을 직접 확인할 수 있는 "최근 교정 목록 뷰(Recent Correction List View)"를 권고함.

## 분석
- **성과**: M61-M66을 통해 상위 반복 패턴의 가시성, 승인, 무시 조작이 완성됨.
- **현 상태**: 운영자는 "상위 패턴"은 볼 수 있지만, 최근에 어떤 개별 교정들이 발생했는지(예: 방금 수정된 1건의 교정)를 추적할 수 있는 "실시간성" 가시성은 부족한 상태임.
- **리스크**: 반복되지 않은(Recurrence < 2) 개별 교정들은 상위 패턴 목록에 나타나지 않으므로, 시스템이 현재 어떤 교정을 수집하고 있는지 즉각적으로 파악하기 어려움.
- **기회**: `CorrectionStore.list_recent()`는 이미 구현되어 있으므로, 이를 엔드포인트로 노출하고 UI에 배치하는 것만으로도 감사(Audit) 능력을 크게 향상시킬 수 있음.

## 권고 사항
`RECOMMEND: implement M67 Axis 1 — correction list recent view`

### 권고 이유
1. **Enhanced Auditability**: 상위 패턴(통계)과 최근 목록(로그)을 동시에 제공하여 교정 루프의 전반적인 건강 상태를 다각도로 확인 가능.
2. **Same-family Visibility**: PreferencePanel 하단에 "최근 교정" 영역을 추가하여, 학습 중인 데이터를 투명하게 공개하는 제품 방향성을 강화함.
3. **Implementation Efficiency**: 이미 존재하는 `list_recent()` 메서드를 재사용하므로, 최소한의 파일 수정(app/handlers, app/web, api/client, PreferencePanel)으로 높은 가치를 창출함.

### 구현 슬라이스
- **Backend**: `GET /api/corrections/list` 엔드포인트 추가 (limit=20 등 파라미터 지원).
- **Frontend**: `api/client.ts`에 `fetchCorrectionList()` 추가. `PreferencePanel.tsx` 하단에 "최근 교정" 섹션을 추가하여 최신 3~5건의 스니펫을 컴팩트하게 표시.

## 결론
집계 통계를 넘어 개별 기록의 흐름을 보여주는 M67 Axis 1 진행을 강력히 권고함.
