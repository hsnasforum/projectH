# 2026-04-25 M36-direction-lifecycle-closure

## 결정: 후보 1 (preference lifecycle 안정화 및 검증 보강)

### 근거
1. **기능적 완결성 (GEMINI.md 우선순위 1)**: M36 Axis 1에서 "일시중지(Pause)"의 즉각적인 효과를 검증했습니다. 이제 이 효과가 브라우저 새로고침(Persistence) 후에도 유지되는지, 그리고 "재개(Resume)" 및 "거절(Reject)" 시 루프가 의도대로 복구되거나 닫히는지 전수 검증하여 "Reviewed-Memory Loop" family를 배포 가능한 수준으로 안정화해야 합니다.
2. **리스크 감소**: 대규모 머지 이후, 선호 상태 전이가 런타임 injection 로직과 정확히 동기화되어 동작함을 보장함으로써 사용자 통제의 신뢰성을 확보합니다.
3. **가이드라인 준수**: `GEMINI.md`의 tie-break 기준인 "same-family current-risk reduction"을 따릅니다. 새로운 family(SQLite 등)로 넘어가기 전 현재 family의 edge case를 정리합니다.

### 권고 Slice (M36 Axis 2)
- **목표**: 선호 일시중지의 영속성 확인 및 재개/거절 기능 효과 E2E 검증.
- **실행 항목**:
    - `e2e/tests/web-smoke.spec.mjs`의 `"badge 클릭"` 시나리오를 다음과 같이 확장:
        1. **Persistence**: 선호 일시중지 후 `page.reload()`를 실행하고, 새로운 메시지 전송 시 여전히 선호가 반영되지 않음을 확인.
        2. **Resume**: `PreferencePanel`에서 해당 선호를 다시 "활성화(Resume)"하고, 이후 메시지에서 선호 반영 뱃지가 다시 나타남을 확인.
        3. **Reject**: 선호를 "거절(Reject)" 처리하고, 이후 세션 및 메시지에서 완전히 제외됨을 확인.
- **검증**: `make e2e-test` (148 scenarios) 전수 PASS 확인.

### 후보 검토
- **후보 2 (새 기능 - SQLite)**: 인프라 전환은 M37의 주요 테마로 설정하여 집중 처리하는 것이 아키텍처 정합성 면에서 유리합니다. 현재는 "Teachable Loop"의 안정적 종결이 우선입니다.
- **후보 3 (유지보수)**: re-export 정리 등은 구조적 phase가 끝난 현재 시점에서 리스크 감소 효과가 상대적으로 낮으므로 후순위로 미룹니다.
