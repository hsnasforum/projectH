# Advisory Log: M14 Axis 2 Definition (Doc-sync + Quality Scoring UI)

## 개요
- **일시**: 2026-04-23
- **요청**: M14 Axis 2 정의 및 exact next slice 추천
- **상태**: Advisory Seq 23에서 추천된 M14 Axis 2(PreferencePanel reliability stats)가 이미 `ebd82cb` (CONTROL_SEQ 16)에서 구현되었으나 `MILESTONES.md`에 반영되지 않은 doc-sync gap 발견.

## 분석 및 판단
1. **Doc-sync Gap**: M13 Axis 5b(frontend reliability stats)가 이미 배포되었음에도 `MILESTONES.md`에는 "frontend display deferred"로 남아 있음. 
2. **Next Slice 후보**:
   - Option A: Doc-sync 전용 라운드 진행 후 M14 Axis 3 진입.
   - Option B: Doc-sync와 M14 Axis 3(Trace Quality Scoring UI)를 하나의 coherent slice로 통합.
3. **판단 근거**: `GEMINI.md`의 "Next slice recommendation은 지나치게 잘게 쪼개지 말고, review 가능한 범위 안에서 의미 있는 진척을 닫는 coherent slice 1개를 우선한다"는 원칙에 따라 Option B를 선택. 단순 문서 수정만으로 한 라운드를 소비하기보다, Milestone 14의 품질 축(Quality Axis)을 강화하는 UI 작업을 병행하는 것이 효율적임.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M14 Axis 2 (Doc-sync + Trace Quality Scoring UI)**

1.  **Documentation Sync**:
    - `docs/MILESTONES.md`의 M13 Axis 5/5b 항목 업데이트. `ebd82cb` (CONTROL_SEQ 16)에서 배포된 frontend reliability stats 기록.
2.  **Core Logic**:
    - `core/delta_analysis.py`에 `is_high_quality(similarity_score: float) -> bool` 헬퍼 추가 (임계값: 0.05 ≤ score ≤ 0.98).
    - `scripts/export_traces.py`에서 로컬 정의된 헬퍼를 `core.delta_analysis` 버전으로 교체.
3.  **Storage Layer**:
    - `PreferenceStore` (JSON/SQLite 모두)의 `record_reviewed_candidate_preference` 및 `promote_from_corrections`가 `similarity_score`(평균값)를 저장하도록 업데이트.
4.  **Backend API**:
    - `app/handlers/preferences.py`의 `list_preferences_payload()`가 각 선호 레코드에 `quality_info` (score 및 `is_high_quality` 여부)를 포함하도록 보강.
5.  **Frontend UI**:
    - `app/frontend/src/components/PreferencePanel.tsx`에서 '검토 후보' 리스트에 고품질(High Quality) 배지 또는 신뢰도 점수 표시 추가.

## 기대 효과
- `MILESTONES.md`와 실제 구현체 간의 drift 해소.
- M12 Axis 3에서 정의된 품질 점수를 사용자 UI에 시각화하여 검토 후보의 수락/거부 판단 근거 강화.
- Milestone 14의 목표인 "Trace Quality Integration"의 가시적 진척 확보.
