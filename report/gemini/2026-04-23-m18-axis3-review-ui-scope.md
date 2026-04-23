# Advisory Log: M18 Axis 3 - Global Candidate Review Interface Scope

## 개요
- **일시**: 2026-04-23
- **요청**: M18 Axis 3 (Review Queue Integration for Global Candidates)의 정확한 범위 및 구현 전략 정의
- **상태**: M18 Axis 2에서 SQLite 기반의 효율적인 반복 패턴 검색(`find_recurring_patterns`)과 서버 연결이 완료됨. 이제 세션 로컬 후보를 넘어, 전체 시스템에서 발견된 반복 패턴을 사용자에게 "글로벌 후보"로 제안할 준비가 됨.

## 분석 및 판단
1.  **글로벌 후보 정의**: 현재 세션의 메시지에서 유도되지 않았더라도, 전체 교정 이력(`CorrectionStore`)에서 2회 이상 발견된 패턴(Fingerprint) 중 아직 선호(`Preference`)로 등록되지 않은 것을 의미함.
2.  **노출 전략**: 별도의 "전역 후보" 탭을 만들기보다, 기존 `ReviewQueuePanel`에 통합하여 노출하되 `범용` 또는 `글로벌` 배지를 통해 구분함. 이는 사용자가 현재 세션 작업 중에도 시스템이 전역적으로 학습한 유용한 규칙을 즉시 수락할 수 있게 함.
3.  **데이터 정합성**: 이미 `PreferenceStore`에 활성/비활성 상태로 존재하는 패턴은 리뷰 큐에서 제외하여 중복 제안을 방지함.
4.  **액션 처리**: 글로벌 후보는 특정 세션 메시지에 종속되지 않으므로(`source_message_id = "global"`), 수락 시 메시지 레벨의 리뷰 기록 단계를 건너뛰고 즉시 선호 저장소로 승격함.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M18 Axis 3 (Global Candidate Review UI)**

1.  **Serializer (Enrichment)**:
    - `app/serializers.py:_build_review_queue_items`에서 `self.correction_store.find_recurring_patterns()` 호출.
    - 검색된 각 패턴에 대해 `self.preference_store.find_by_fingerprint()`를 수행하여 중복 여부 확인.
    - 미등록 패턴을 `ReviewQueueItem`으로 변환:
        - `source_message_id`: `"global"` (고정 식별자)
        - `candidate_id`: `"global:{fingerprint}"`
        - `is_global`: `True`
        - `statement`: 해당 패턴의 최신 교정 문구 또는 기본값.
        - `quality_info`, `delta_summary`, `snippets`: 해당 패턴의 대표 교정본에서 추출.
2.  **Frontend (UI)**:
    - `app/frontend/src/api/client.ts`: `ReviewQueueItem` 인터페이스에 `is_global?: boolean` 추가.
    - `ReviewQueuePanel.tsx`: `is_global`이 참인 항목 옆에 `범용` 배지 표시 (청색 계열).
3.  **Backend Handler (Action)**:
    - `app/handlers/aggregate.py:submit_candidate_review` 수정.
    - `source_message_id == "global"`인 경우 `session_store` 기록 단계를 생략하고, `candidate_id`에서 fingerprint를 추출하여 `preference_store.record_reviewed_candidate_preference` 바로 호출.
4.  **Validation**:
    - Playwright 시나리오: 서로 다른 세션에서 동일 교정 2회 생성 -> 세션 로드 시 리뷰 큐에 `범용` 항목 노출 확인 -> 수락 클릭 -> 선호 기억 패널에 등록 확인.

## 기대 효과
- 사용자가 과거 세션에서 반복했던 교정 행위를 현재 세션에서 즉시 시스템 규칙으로 확정 가능.
- "한 번의 실수가 세션 간 장벽을 넘어 바로 학습으로 이어지는" 진정한 개인화 경험 제공.
- Milestone 18의 "Cross-Session Signal Infrastructure" 목표 완결.
