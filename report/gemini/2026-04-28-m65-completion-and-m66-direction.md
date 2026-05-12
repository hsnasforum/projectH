# Advisory Log: 2026-04-28 — M65 완료 및 M66 방향 권고

## 개요
M65 Axis 1 완료를 통해 `SQLiteCorrectionStore`의 패리티가 복구되었으며, `/api/corrections/summary` 및 `confirm-pattern`이 기본 설정에서 정상 작동함. 다음 마일스톤 M66에서는 "승인(Confirm)"의 대칭 동작인 "무시(Dismiss)" 기능을 추가하여 교정 분석 검증 UI를 완성할 것을 권고함.

## 분석
- **성과**: M65를 통해 기술적 부채(SQLite parity)를 해소하여 안정적인 베이스라인을 확보함.
- **현 상태**: 운영자가 반복 패턴을 보고 "승인"할 수는 있지만, 불필요한 패턴이나 노이즈를 "무시"하여 목록에서 제거하거나 상태를 정리할 방법이 부재함.
- **기회**: `dismiss_by_fingerprint()`를 추가하여 특정 패턴을 일괄 `STOPPED` 상태로 전이시키고, 이를 UI에 "무시" 버튼으로 노출함으로써 운영 효율성을 높일 수 있음.

## 권고 사항
`RECOMMEND: implement M66 Axis 1 — correction pattern dismiss`

### 권고 이유
1. **Functional Completeness**: 승인/무시의 대칭 구조를 갖춤으로써 교정 패턴 검증(Validation)의 기본 워크플로우를 완성함.
2. **Signal Noise Reduction**: 무시된 패턴을 `STOPPED` 상태로 관리하여, 분석 결과에서 제외하거나 신뢰도 계산 시 무시할 수 있는 근거를 마련함.
3. **Parity First Strategy**: M65의 교훈을 반영하여, JSON과 SQLite 구현을 Axis 1 단계에서 동시에 진행하여 기술적 일관성을 유지함.

### 구현 슬라이스
- **Storage**: `CorrectionStore` 및 `SQLiteCorrectionStore`에 `dismiss_by_fingerprint()` 추가.
- **Backend**: `POST /api/corrections/dismiss-pattern` 엔드포인트 신설.
- **Frontend**: `PreferencePanel.tsx` 상위 패턴 라인에 "무시" 버튼 추가 및 `confirmCorrectionPattern` 대칭 API 연결.

## 결론
교정 분석 도구의 조작성(Control)을 완성하는 M66 Axis 1 진행을 강력히 권고함.
