# 2026-04-25 M37-axis2-preference-lifecycle-closure

## 결정: 후보 A (preference resume/reject lifecycle E2E)

### 근거
1. **기능적 완결성 확보 (GEMINI.md 우선순위 1)**: Milestone 35-36을 통해 "일시중지(Pause)" 및 "영속성(Persistence)"을 검증했습니다. 하지만 루프의 나머지 상태인 "재개(Resume)"와 "거절(Reject)"은 아직 E2E 수준에서 기능적 효과(injection 복구 및 영구 제외)가 검증되지 않았습니다. 이를 완료하여 "Teachable AI" 루프의 전체 생명주기를 확정합니다.
2. **테스트 안정성 강화**: M36에서 지연되었던 누적 DB 환경(accumulated DB)에서의 flakiness 문제를 "API 직접 호출(API-direct)" 방식으로 해결합니다. 이는 UI 상태에만 의존하는 것보다 더 견고하며, 향후 인프라 변경에도 강한 검증 기반을 제공합니다.
3. **가이드라인 준수**: `GEMINI.md`의 tie-break 기준인 "same-family current-risk reduction"을 따릅니다. 새로운 기능 family(M38 예정)로 넘어가기 전 현재 family의 검증 부채를 완전히 해소합니다.

### 권고 Slice (M37 Axis 2)
- **목표**: 선호의 재개(Resume) 및 거절(Reject) 기능이 런타임 injection에 미치는 효과를 API 기반으로 전수 검증.
- **실행 항목**:
    1. **Resume 검증**: `page.request.post("/api/preferences/activate")`를 통해 일시중지된 선호를 재활성화한 후, 새로운 메시지 전송 시 "Applied Preference" 뱃지가 다시 나타나는지 확인.
    2. **Reject 검증**: `page.request.post("/api/preferences/reject")`를 통해 선호를 영구 거절한 후, 새로고침 및 세션 재로드 후에도 해당 선호가 응답 및 관리 목록에서 사라지는지 확인.
    3. **Robust Assertion**: 특정 `preference_id`를 추적하고, count-based assertion을 병행하여 누적된 데이터베이스 상태에서도 정확한 결과 도출.
- **검증**: `make e2e-test` (148 scenarios) 및 isolated lifecycle smoke PASS 확인.

### 후보 검토
- **후보 B (새 기능)**: SQLite 전환이 완료된 시점에서 기능 확장을 고려할 수 있으나, 현재 "검증된 루프"를 완성하는 것이 리스크 관리 면에서 우선입니다.
- **후보 C (기술 부채)**: re-export 정리 등은 구조적 완성도를 높이지만, 사용자 가치와 기능적 무결성을 증명하는 후보 A의 시급성이 더 높습니다.
