# Advisory Log: 2026-04-28 — M69 완료 및 M70 구조 개선(Structural) 방향 권고

## 개요
M61–M69로 이어지는 "교정 생명주기(Correction Lifecycle)" Axis가 검색 및 충돌 감지 기능 구현과 E2E 검증을 끝으로 실질적으로 완료되었습니다. 현재 프로젝트는 "v1.5 structural" 단계에 있으며, 이는 기능적 완성도를 바탕으로 시스템의 구조적 부채를 해결하고 안정성을 높이는 데 집중하는 시기입니다. 본 advisory는 비대해진 핸들러 계층을 정리하고 유지보수성을 확보하기 위한 M70 구조 개선 슬라이스를 권고합니다.

## 분석 및 상태 확인
- **M69 성과**: 교정 기록에 대한 필터링 검색과 활성 선호도와의 충돌 신호 표시가 완료되었습니다. (verify CONTROL_SEQ 1245)
- **코드 비대화**: M61–M69를 거치며 `app/handlers/aggregate.py`가 약 940라인으로 증가했습니다. 특히 교정 관련 메서드들이 독립적인 생명주기를 가짐에도 불구하고 `AggregateHandlerMixin`에 섞여 있어 응집도가 떨어지고 있습니다.
- **백로그 현황**: `CorrectionRecord`의 물리적 검증(Physical validation)이 아직 미완 상태이며, 이는 구조 개선 단계에서 데이터 정합성을 확보하기 위한 핵심 과제입니다.

## 권고 사항
`RECOMMEND: structural M70 Axis 1 — Correction Handler Structural Decomposition`

### 권고 근거
1. **내부 정리 (Internal Cleanup)**: 비대해진 `aggregate.py`를 분리하여 `PreferenceHandlerMixin`과 유사한 독립적인 핸들러 구조를 확보합니다. (v1.5 structural 단계 지침 준수)
2. **응집도 향상**: 교정 요약, 목록, 승인, 무시, 승격 등 교정 전용 로직을 `app/handlers/corrections.py`로 모아 관리 효율성을 높입니다.
3. **확장성 확보**: 향후 "물리적 검증(Physical validation)"이나 "교정 기반 분석" 기능을 추가할 때 깨끗한 진입점을 제공합니다.

### M70 Axis 1 상세 가이드
- **작업 내용**:
  - `app/handlers/corrections.py` 신규 생성.
  - `AggregateHandlerMixin`에서 교정 관련 메서드(summary, list, confirm, dismiss, promote) 및 관련 헬퍼(`_first_correction_snippets`)를 `CorrectionHandlerMixin`으로 추출.
  - `app/web.py`의 `WebAppService`가 신규 `CorrectionHandlerMixin`을 상속받도록 수정.
- **기대 효과**: `aggregate.py`를 약 200~300라인 수준으로 경량화하고, 핸들러 계층의 책임을 명확히 분리합니다.

## 결론
기능 추가보다는 구조적 부채 해결이 우선인 현재 단계에서, M70 Axis 1은 시스템의 장기적 안정성을 위한 필수적인 슬라이스입니다. 현재 작업트리에 남은 M69 변경분(11개 파일)을 먼저 커밋/푸시하여 백로그를 정리한 후 작업을 시작할 것을 권장합니다.
