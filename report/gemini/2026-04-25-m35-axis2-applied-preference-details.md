# 2026-04-25 M35-axis2-applied-preference-details

## 결정: 후보 1 (preference lifecycle 완성도 개선 — 상세 정보 노출 및 인라인 편집)

### 근거
1. **투명성 및 신뢰성 (North Star)**: 사용자가 "선호 N건 반영" 뱃지를 보았을 때, 단순히 반영되었다는 사실을 넘어 "어떤 원본이 어떻게 수정되었는지(Snippet)"를 즉시 확인할 수 있게 함으로써 시스템의 판단 근거를 투명하게 공개합니다.
2. **피드백 루프 단축 (User-Visible Improvement)**: 시스템이 잘못된 이유로 선호를 적용했다고 판단될 경우, 별도의 관리 화면으로 이동하지 않고도 뱃지 팝오버에서 즉시 설명을 수정(Edit)하거나 중단(Pause)할 수 있는 인라인 제어 능력을 제공합니다.
3. **가이드라인 준수**: `GEMINI.md`의 "same-family user-visible improvement" 원칙에 따라 M34~M35에서 구축한 "Reviewed-Memory Loop"의 사용자 체감 품질을 극대화합니다.

### 권고 Slice (M35 Axis 2)
- **목표**: 적용된 선호 뱃지의 팝오버에 상세 정보(Original/Corrected Snippet)를 노출하고 인라인 설명 편집 기능을 추가.
- **실행 항목**:
    1. **Frontend Data**: `MessageBubble.tsx`에서 팝오버가 열릴 때 전체 선호 목록을 가져와(`fetchPreferences`) 현재 메시지에 적용된 지문(fingerprint)과 일치하는 상세 레코드를 조회.
    2. **Snippet 노출**: 팝오버 내 각 선호 항목에 대해 `original_snippet` 및 `corrected_snippet`이 존재하는 경우, 이를 "변경 전/후" 형식으로 작게 표시.
    3. **인라인 편집**: 팝오버 내에서 선호 설명을 즉시 수정할 수 있는 입력란과 저장 버튼 추가 (`POST /api/preferences/update-description` 호출).
    4. **E2E 검증**: 뱃지 클릭 시 팝오버에 스니펫이 정상적으로 보이는지, 설명 수정 후 반영되는지 검증하는 시나리오 보강.
- **검증**: `make e2e-test` (148 scenarios) 및 브라우저 매뉴얼 확인.

### 후보 검토
- **후보 2 (새 기능 - SQLite 전환)**: 인프라 부채 해결은 중요하나, 현재 사용자에게 가시적인 "Teachable AI" 경험을 완성하는 것이 제품 전략상 더 우선순위가 높습니다.
- **후보 3 (유지보수)**: Watcher re-export 정리는 시스템 안정성에는 기여하나 사용자 가치 증대는 적으므로, 기능 완성 후 opportunistic하게 처리합니다.
