# Advisory Log: 2026-04-28 — M73 완료 및 M74 아티팩트·태스크 로그 물리 검증(Validation Bundle) 방향 권고

## 개요
M73 Axis 1을 통해 선호도 스토어(`PreferenceStore`)의 물리 검증 레이어가 성공적으로 구축되었습니다. 이로써 교정(Correction)과 선호도(Preference)라는 핵심 메모리 계층의 데이터 정합성 가드레일이 확보되었습니다. 본 advisory는 "v1.5 structural" 단계의 데이터 계층 안정화 작업을 마무리하기 위해, 남은 주요 저장소인 아티팩트(`ArtifactStore`)와 태스크 로그(`TaskLog`)에 대한 검증을 번들로 처리하는 M74 방향을 권고합니다.

## 분석 및 상태 확인
- **M73 성과**: `PreferenceStore`의 읽기 경로에서 필수 필드가 누락된 레코드를 필터링하여 프롬프트 주입의 신뢰도를 높였습니다. (verify CONTROL_SEQ 1261)
- **현 상황**:
  - `ArtifactStore`는 브라우저 MVP의 핵심 결과물(Grounded Brief 등)을 저장하지만, 현재 `artifact_id` 존재 여부만으로 데이터를 로드하고 있습니다.
  - `TaskLogger`는 JSONL 형식을 사용하며 기본적인 파싱 오류는 잡고 있으나, 필수 비즈니스 필드(session_id, action 등)의 존재를 강제하지 않습니다.
- **v1.5 Structural 우선순위**: "v1.5 structural" 단계의 목표인 "internal cleanup"을 완수하기 위해, 모든 주요 로컬 저장소의 읽기 경로에 동일한 수준의 물리 검증 패턴을 적용하여 데이터 계층의 부채를 완전히 해소해야 합니다.

## 권고 사항
`RECOMMEND: implement M74 Axis 1 — Artifact & Task Log Physical Validation Bundle`

### 권고 근거
1. **데이터 계층 완결성 (Structural Hardening)**: 모든 주요 스토어(Correction, Preference, Artifact, Task Log)에 일관된 검증 패턴을 적용하여 "Memory Phase"의 물리적 안정성을 완성합니다. (Priority 1: same-family risk reduction)
2. **번들링 효율성**: 아티팩트와 태스크 로그는 상대적으로 구조가 단순하여 개별 마일스톤보다는 하나의 번들로 처리하는 것이 효율적입니다.
3. **v1.5 지침 준수**: 기능 추가를 배제하고 기존 인프라를 견고하게 다지는 작업으로, 이후 Axis 3(신뢰도)나 대규모 기능 전환을 위한 깨끗한 데이터 상태를 보장합니다.

### M74 Axis 1 상세 가이드
- **작업 내용**:
  - `storage/artifact_store.py`: `_is_valid_artifact_record()` 추가 및 `list_by_session`, `list_recent` 필터 적용. (필수 필드: `artifact_id`, `artifact_kind`, `session_id`, `created_at`)
  - `storage/task_log.py`: `log` 레코드의 필수 필드 검증 및 `iter_session_records`에서 malformed 라인 제외 강화. (필수 필드: `ts`, `session_id`, `action`)
  - `storage/sqlite_store.py`: `SQLiteArtifactStore`의 읽기 경로에도 동일한 validator 적용.
- **검증 범위**: 필수 필드 존재 여부 및 기본 타입 체크.

## 결론
M72–M73으로 구축된 검증 체계를 아티팩트와 로그 계층으로 확장하여 "Structural Hardening"을 마무리하는 M74 Axis 1 진행을 권고합니다. 이 작업이 완료되면 다음 단계로 전반적인 Truth-Sync(M75) 또는 신규 기능 Axis로의 전환이 가능해질 것입니다.
