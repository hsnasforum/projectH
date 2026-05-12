# 2026-04-30 M110 다음 슬라이스 방향 권고: 검토 대기열 UX 강화

## STATUS: advice_ready
## CONTROL_SEQ: 1489
## 슬러그: m110-review-queue-ux

## 요약

Functional Parity (Correction ↔ Preference) 아크 완결 후, 다음 논리적 단계로 **검토 대기열(Review Queue)의 가시성 및 관리 기능 강화(Choice A)**를 권고합니다.

## 판단 근거

1. **Functional Parity 완결**: M109를 통해 Correction History와 Preferences 양쪽 도메인의 핵심 기능(Detail, Filter, Search, Pagination) 대칭이 완료되었습니다. 현재 PR #91–#101이 적체된 상태이나, 이는 operator_merge_gate 영역이므로 advisory는 다음 설계 방향에 집중합니다.
2. **검토 대기열의 중요성**: 검토 대기열은 교정(Correction)에서 선호(Preference)로 전이되는 핵심 관문입니다. 현재 인프라는 "shipped" 상태이나 UI는 최소 기능만 갖춘 상태(Compact)입니다.
3. **리스크 감소 및 가시성 확보**: 후보군(Candidate)이 누적됨에 따라 검색, 상태 필터, 대기 건수 배지, 검토 결과(적용/중단/되돌리기)의 가시성이 누락되면 운영 복잡도가 급격히 증가합니다. 이는 `GEMINI.md`의 "same-family current-risk reduction" 기준에 부합합니다.
4. **단계적 확장**: Cross-session memory 강화로 가기 전, 현재 세션 내의 검토 프로세스를 유저가 명확히 제어할 수 있는 상태로 만드는 것이 안정적인 발전 경로입니다.

## 권고 사항

- **RECOMMEND: implement A) reviewed-memory / review queue UX 강화**
- **Exact Slice**:
    - 검토 대기열 내 검색(Search) 및 상태 필터(Filter) 추가
    - 대기 중인 항목 수 표시(Pending Badge)
    - 검토 결과 및 적용 상태(active-effect)의 UI 가시성 개선

## 리스크 및 주의사항

- PR 머지 백로그(#91-#101)가 해소되지 않은 상태에서 신규 로직이 섞이지 않도록 `feat/m110-review-queue-ux` 브랜치를 별도 관리할 것을 권장합니다.
- 기존 `reviewed_memory_boundary_draft` 계약을 준수하며, UX 레이어 위주의 개선에 집중하여 복잡도를 관리해야 합니다.
