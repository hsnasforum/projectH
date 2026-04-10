# docs: response-origin summary richness family 종료 및 차기 구현 슬라이스 중재

## 상황 요약
- `docs/PRODUCT_PROPOSAL.md`, `docs/project-brief.md`, `docs/PRODUCT_SPEC.md` 등 root-doc 전반의 `response-origin summary richness` 관련 wording 동기화와 Korean badge labels 반영이 완료되었습니다.
- Codex는 해당 family의 docs-only truth-sync가 충분히 반복되었다고 판단하고, Milestone 4 (Secondary-Mode Investigation Hardening)의 후보군 중 다음 `app.web` 구현 슬라이스를 고르는 데 어려움을 겪고 있습니다.

## 중재 결과
- **RECOMMEND: implement `claim-based entity-card shaping`**

## 판단 근거
1. **Axis Transition:** 동일 family 내의 docs-only 작업이 이미 여러 차례 반복되어 root-doc 간의 truth-sync가 견고해졌습니다. 이제는 문서 보강보다 새로운 품질 축(Quality Axis)인 Milestone 4 구현으로 전환할 시점입니다.
2. **User-Visible Priority:** 후보군(`multi-source agreement`, `reinvestigation logic`, `fact-strength distinction` 등) 중 `entity-card shaping`은 사용자가 richness를 직접 체감할 수 있는 가장 가시적인 UI/UX 개선 항목입니다.
3. **Continuity:** 앞선 docs 작업에서 정의한 `설명 카드` / `최신 확인` 등의 richness를 실제 response surface에 "shaping"하는 작업은 작업의 맥락적 일관성이 가장 높습니다.
4. **Risk Management:** 내부 로직(agreement/reinvestigation)을 먼저 건드리기보다, 그것이 표현될 그릇(entity-card shaping)을 먼저 확정하는 것이 차후 로직 변경에 따른 UI 검증을 더 용이하게 합니다.

## 차기 단계
- Codex는 이 권고를 바탕으로 `.pipeline/claude_handoff.md`에 `claim-based entity-card shaping` 구현 지시를 남기고 다음 라운드를 시작해야 합니다.
