# Advisory Log: 2026-04-28 — M72 완료 및 M73 선호도 스토어 물리 검증(Physical Validation) 방향 권고

## 개요
M72 Axis 1을 통해 교정 스토어(`CorrectionStore`)의 물리 검증 레이어가 성공적으로 구현 및 검증되었습니다. 이는 "v1.5 structural" 단계의 핵심 목표인 데이터 계층 안정화의 첫 단추를 꿰었습니다. 본 advisory는 교정 데이터의 최종 결과물이며 모델 응답 생성에 직접적인 영향을 미치는 선호도 스토어(`PreferenceStore`)에 대해서도 동일한 수준의 물리 검증을 확장하는 M73 방향을 권고합니다.

## 분석 및 상태 확인
- **M72 성과**: `CorrectionStore`의 읽기 경로(`_scan_all`, `list_recent`, `list_filtered`)에서 필수 필드가 누락된 레코드를 자동으로 필터링하는 가드레일을 구축했습니다. (verify CONTROL_SEQ 1257)
- **현 상황**: `PreferenceStore` 및 `SQLitePreferenceStore`는 현재 `preference_id` 존재 여부만으로 레코드를 식별하고 있습니다. 선호도 데이터는 모델 프롬프트 주입(Injection)의 소스로 사용되므로, 데이터 손상이나 필드 누락이 발생할 경우 런타임 응답 생성 실패로 이어질 위험이 큽니다.
- **v1.5 Structural 우선순위**: "v1.5 structural" 단계의 지침인 "internal cleanup" 및 "risk reduction"에 따라, 핵심 메모리 스토어들의 읽기 경로에 대한 정합성 검사를 완료하여 인프라의 신뢰도를 높여야 합니다.

## 권고 사항
`RECOMMEND: implement M73 Axis 1 — Preference Store Physical Validation`

### 권고 근거
1. **위험 감소 (Risk Reduction)**: 프롬프트 주입의 핵심 소스인 선호도 레코드의 정합성을 보장하여 런타임 응답 생성의 안정성을 확보합니다. (Priority 1: same-family risk reduction)
2. **패턴 일관성 (Consistency)**: M72에서 확립된 `_is_valid_*_record` 패턴을 `PreferenceStore`에도 적용하여 코드베이스의 일관성을 유지합니다.
3. **v1.5 지침 준수**: 기능 추가를 최소화하고 기존 구조의 안정성을 극대화하는 "structural hardening" 작업의 연속선상에 있습니다.

### M73 Axis 1 상세 가이드
- **작업 내용**:
  - `storage/preference_store.py`에 `_is_valid_preference_record()` 유틸리티 함수 구현 (필수 필드: `preference_id`, `delta_fingerprint`, `status`, `created_at` 등).
  - `PreferenceStore._scan_all()` (JSON) 및 `SQLitePreferenceStore.get_active_preferences()` 등 읽기 경로에 필터 적용.
  - `storage/sqlite_store.py`에서 공통 validator 활용.
- **검증 범위**: 필수 필드 존재 여부, 상태(`PreferenceStatus`)의 유효성, 타임스탬프 형식 등.

## 결론
교정 Axis에 이어 선호도 Axis의 데이터 정합성을 확보하는 M73 Axis 1 진행을 권고합니다. 이는 향후 모델 주입 신뢰도(Axis 3)를 논의하기 위한 필수적인 데이터 계층 안정화 단계입니다.
