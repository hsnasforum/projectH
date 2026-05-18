# 2026-04-26 Milestone 39 종결 및 Milestone 40 Axis 1 권고

## 상황 개요
- **Milestone 39 (Review Evidence Enrichment) 완료**: `context_turns`(Axis 1)와 `evidence_summary`(Axis 2) 구현 및 `docs/MILESTONES.md` 동기화(Axis 3)가 완료되어 Milestone 39가 공식적으로 종결되었습니다.
- **차기 목표**: **Milestone 40: Review Auditability**로 진입하여 학습된 지식(Preference)의 출처와 판단 근거에 대한 투명성을 강화합니다.
- **현상**: 현재 리뷰 큐(Review Queue)의 후보들은 어느 세션에서 발생했는지에 대한 정보가 UI에 노출되지 않아, 특히 범용(Global) 후보의 경우 출처 맥락을 파악하기 어렵습니다.

## 판단 근거
1. **운영 투명성(Auditability)**: 리뷰 후보와 원본 세션 간의 연결(Deep link)은 학습된 데이터의 신뢰성을 검증하는 데 필수적입니다.
2. **범용 후보 맥락 보강**: M39에서 추가된 '대화 맥락'은 특정 메시지 주변의 텍스트를 보여주지만, 해당 대화가 어떤 주제(세션 제목)였는지 아는 것은 운영자가 선호의 일반화 가능성을 판단하는 데 큰 도움이 됩니다.
3. **M40 전략적 시작**: M40의 첫 번째 단계로 '세션 연결'을 구현하여 데이터 모델의 감사 가능성(Auditability) 베이스라인을 구축합니다.

## 권고 사항 (RECOMMENDATION)
- **결정**: Milestone 39를 종결하고 **Milestone 40 Axis 1** 구현을 시작합니다.
- **RECOMMEND: implement Milestone 40 Axis 1: Review Auditability — Source Session Association**
    - `serializers.py`: `ReviewQueueItem`에 `source_session_id`와 `source_session_title` 필드를 추가합니다.
    - `ReviewQueuePanel.tsx`: 리뷰 아이템 하단에 원본 세션 제목을 표시하여 운영자가 출처를 즉시 인지할 수 있게 합니다.
    - 범용(Global) 후보의 경우, 가장 최근에 기여한 세션 또는 대표 세션 정보를 포함합니다.

### 예상 결과
- 운영자가 리뷰 후보의 출처 세션을 즉시 확인할 수 있어 판단의 정확도 향상.
- 학습된 선호 기록에 대한 감사(Audit) 경로 확보.
- Milestone 40의 두 번째 단계인 '결정 사유(Rationale) 캡처'를 위한 기초 데이터 확보.
