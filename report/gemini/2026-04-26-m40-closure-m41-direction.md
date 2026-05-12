# 2026-04-26 M40 종결 및 M41 방향 권고 — Preference 감사 가시성 강화

## 상황 개요
- **Milestone 40 (Review Auditability) 구현 완료**: Axis 1(Source Session Association)과 Axis 2(Decision Rationale Capture)를 통해 리뷰 결정의 출처와 사유를 기록하는 인프라를 구축했습니다.
- **문서 동기화 필요**: Milestone 40의 실제 구현 상태를 `docs/MILESTONES.md`에 반영하여 베이스라인을 정리해야 합니다.
- **차기 목표**: 기록된 감사 데이터를 실제 운영 화면인 '선호 기억(Preference Panel)'에 노출하여, 학습된 지식의 투명성을 사용자/운영자에게 완결성 있게 전달합니다.

## 판단 근거
1. **Truth-Sync 유지**: M40의 성공적인 구현(Axes 1–2)을 공식 문서에 기록하여 프로젝트 상태의 정합성을 유지합니다.
2. **감사 루프 완성**: M40에서 '기록'된 사유(Rationale)와 세션 출처는 현재 '선호 기억' 패널에서 조회할 수 없습니다. 이를 노출함으로써 "왜 이 선호도가 생겼는가"에 대한 운영자의 의문을 해소할 수 있습니다.
3. **학습 신뢰도 향상**: 선호도 항목과 원본 대화(세션 제목) 및 승인 당시의 코멘트를 연결하면, 시스템이 사용자의 의도를 올바르게 학습했는지 검증하기 훨씬 수월해집니다.

## 권고 사항 (RECOMMENDATION)
- **결정**: Milestone 40을 공식 종결하고 **Milestone 41: Preference Auditability & Visibility**로 진입합니다.
- **RECOMMEND: implement Milestone 40 Axis 3: Doc-Sync Closure**
    - `docs/MILESTONES.md`: Milestone 40을 'Completed'로 이동하고 상세 내역을 갱신합니다.
- **차기 단계 (M41)**: **Milestone 41: Preference Auditability — Trace Visibility in PreferencePanel**
    - **Axis 1**: `PreferencePanel.tsx`에서 각 선호도 항목의 '결정 사유(Rationale)'와 '원본 세션 제목'을 노출합니다.

### 예상 결과
- 프로젝트 문서와 실제 코드 상태의 일치(Truth-Sync).
- '선호 기억' 화면에서 각 규칙의 생성 배경(누가, 왜, 어디서 승인했는지)을 즉시 파악 가능.
- 학습된 데이터의 사후 관리 및 신뢰도 검증 효율성 대폭 향상.
