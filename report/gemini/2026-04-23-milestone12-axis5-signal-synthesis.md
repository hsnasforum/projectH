# 2026-04-23 Milestone 12 Preference Signal Synthesis

## 요약
- Milestone 12 Axis 4(Asset Promotion) 완료 후, 137개의 교정 쌍이 공식 자산으로 승격되었습니다.
- 하지만 현재 자산은 "교정(Correction)"에만 치우쳐 있으며, 사용자의 명시적 선호도가 담긴 **피드백(Feedback)과 반복 패턴(Preference)**이 내보내기 및 감사 프로세스에서 누락되어 있습니다.
- 다음 슬라이스로 **Preference & Feedback Signal Synthesis (Axis 5)**를 권고하며, 이를 통해 "Correction Memory"와 "Preference Memory"를 통합한 완전한 개인화 데이터셋을 구축합니다.

## 권고 사항 (Milestone 12 Axis 5: Multi-Signal Asset Integration)

단순 교정 쌍을 넘어 사용자의 만족도와 반복되는 선호 패턴을 데이터셋에 통합하여 Milestone 12의 "Personalization Assets" 품질을 완성합니다.

### 핵심 변경 내용
1. **피드백 메타데이터 결합**: `storage/session_store.py`의 `stream_trace_pairs()`가 각 메시지의 `feedback` 객체를 함께 반환하도록 수정합니다. (seq 934 권고 사항의 미이행분 완료)
2. **선호도 자산 내보내기**: `scripts/export_traces.py`를 확장하여 `PreferenceStore`의 `CANDIDATE` 및 `ACTIVE` 레코드를 별도의 섹션이나 통합된 JSONL 포맷으로 추출합니다.
3. **Audit 유틸리티 정교화**: `scripts/audit_traces.py`가 `PreferenceStore`의 통계(Candidate/Active 수)를 포함하도록 업데이트하여 Milestone 12 전제 조건인 "enough preference traces"를 정확히 판정하게 합니다.
4. **품질 필터 강화**: `is_high_quality` 판정 시 유사도 점수뿐만 아니라 `helpful` 피드백이 있는 경우 가중치를 부여하거나 우선 순위를 높입니다.

### 테스트 전략
- `tests/test_export_utility.py`에서 피드백과 선호도 데이터가 포함된 복합 데이터셋이 정확히 생성되는지 확인합니다.
- `audit_traces.py` 실행 시 `data/preferences/`의 실제 파일 수와 일치하는 통계가 출력되는지 검증합니다.

## 판단 근거
- **데이터 루프 완결**: 개인화 모델 레이어(Personalization Layer)는 "고쳐야 할 것"뿐만 아니라 "유지해야 할 것"에 대한 신호가 필요합니다. 현재 27개의 선호도 레코드가 존재함에도 감사 결과에 반영되지 않는 점은 시급히 해결해야 할 가시성 격차(Visibility Gap)입니다.
- **Precondition 충족 입증**: 선호도 데이터를 감사 범위에 포함시킴으로써 Milestone 12의 모든 전제 조건이 "Met" 상태임을 공식적으로 선언하고 다음 마일스톤으로 넘어갈 수 있는 근거를 마련합니다.
