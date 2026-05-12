# Advisory Log: 2026-04-28 — M71 완료 및 M72 교정 스키마 물리 검증(Physical Validation) 방향 권고

## 개요
M61–M70으로 이어지는 "교정 생명주기(Correction Lifecycle)" 구현 및 구조 개선(Handler Decomposition) 작업이 완료되었습니다. M71 문서 동기화(Doc-Sync)를 통해 프로젝트 가시성이 확보되었으며, 현재 프로젝트는 "v1.5 structural" 단계의 지침에 따라 구조적 안정성을 최우선으로 하고 있습니다. 본 advisory는 교정 데이터의 런타임 정합성을 보장하기 위한 M72 물리 검증 슬라이스를 권고합니다.

## 분석 및 상태 확인
- **M71 완료**: `MILESTONES.md`와 `TASK_BACKLOG.md`가 최신 상태로 동기화되었습니다 (verify CONTROL_SEQ 1253).
- **잔여 부채**: `TASK_BACKLOG.md`의 "Not Implemented" 항목 중 "correction-memory schema — physical validation"이 여전히 남아 있습니다. 현재 `CorrectionRecord`는 `TypedDict`를 통한 정적 타입 힌트만 제공할 뿐, 실제 저장 및 로드 시 필드 누락이나 타입 불일치를 검사하는 런타임 물리 검증이 누락되어 있습니다.
- **v1.5 Structural 우선순위**: "Ordinary next-step"에서 자동화 안정성을 높이기 위해서는 데이터 계층의 견고함이 필수적입니다. 교정 데이터를 프롬프트에 주입(M49+)하기 전에, 저장된 데이터가 스키마를 완벽히 준수하는지 확인하는 가드레일이 필요합니다.

## 권고 사항
`RECOMMEND: implement M72 Axis 1 — Correction Schema Physical Validation`

### 권고 근거
1. **데이터 정합성 확보 (Risk Reduction)**: 저장된 교정 데이터가 런타임 스키마를 준수하는지 강제함으로써 예기치 못한 타입 오류를 방지합니다 (Priority 1: same-family risk reduction).
2. **구조적 완성**: M61–M70으로 완성된 기능적 생명주기에 "물리적 신뢰도"를 더해 해당 Axis를 완전히 종결합니다.
3. **v1.5 지침 준수**: 새로운 기능(Axis 3 등)으로 넘어가기 전, 기존 인프라를 단단하게 다지는 "structural hardening" 작업입니다.

### M72 Axis 1 상세 가이드
- **작업 내용**:
  - `storage/correction_utils.py` 신규 생성 또는 `storage/correction_store.py` 내부에 `validate_correction_record()` 유틸리티 함수 구현.
  - `CorrectionStore` (JSON) 및 `SQLiteCorrectionStore`에서 데이터를 기록하거나 로드할 때 해당 필드 존재 여부 및 타입을 검증.
  - 스키마 위반 시 적절한 예외 처리 또는 로깅 전략 수립.
- **검증 범위**: 필드 누락, `CandidateFamily` 유효성, 타임스탬프 형식, 재현 횟수(`recurrence_count`)의 정수 여부 등.

## 결론
M71을 통해 정리된 베이스라인 위에서, 교정 데이터 계층의 물리적 신뢰성을 확보하는 M72 Axis 1 진행을 권고합니다. 이는 향후 선호도 주입 자동화의 안전한 토대가 될 것입니다.
