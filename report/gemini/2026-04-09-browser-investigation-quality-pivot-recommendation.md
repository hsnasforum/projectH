# Gemini Advisory: browser investigation quality pivot recommendation (2026-04-17)

## 1. 상황 요약
- **Internal Cleanup 종료**: `CONTROL_SEQ: 281` 슬라이스에서 `docs/projectH_pipeline_runtime_docs/` 5개 문서의 adoption/cutover cleanup이 완료되었습니다. `docs/TASK_BACKLOG.md:155`에서 지시한 잔여 drift가 해소되었으며, 현재 운영 기준(`RUNBOOK §3.5`)과의 정합성이 확보되었습니다.
- **Next Axis Ambiguity**: `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md` 및 `06_ADR_아키텍처_결정기록.md`에 유사한 drift가 남아 있을 가능성은 있으나, 이는 우선순위가 낮은 `internal cleanup` 축입니다.
- **우선순위 재설정**: `GEMINI.md`의 tie-break order(`current-risk reduction > same-family user-visible improvement > new quality axis > internal cleanup`)에 따라, 이제 `internal cleanup`에서 벗어나 사용자에게 더 가치 있는 `same-family user-visible improvement` 또는 `current-risk reduction`으로의 전환이 필요한 시점입니다.

## 2. Arbitration 결과
- **Internal Cleanup Closure**: 현재 docs cleanup은 이 정도로 충분하며, 추가적인 docs micro-slice를 생산하기보다는 주력 품질 축으로 복귀하는 것이 타당합니다.
- **Next Axis Recommendation**: **Browser/user-visible investigation quality** 축으로 복귀합니다. 특히 `entity-card` 모드의 재조사 품질 개선을 제안합니다.

## 3. 권고 Slice
- **RECOMMEND: implement improve entity-card reinvestigation target selection for unresolved slots**
- **이유**: 백로그의 `Current Phase In Progress` 중 "Reinvestigate weak or unresolved slots more effectively" 항목에 해당하며, 사용자에게 노이즈 없는 고품질 정보를 제공하는 `same-family user-visible improvement`에 직결됩니다.
- **Strict Scope Limits**:
  - `core/web_claims.py` 내의 재조사 대상 선정 휴리스틱(selection heuristic)만 수정합니다.
  - UI 레이아웃 변경이나 새로운 모드 추가는 포함하지 않습니다.
  - 현재 권한 게이트가 적용된 `web investigation` 모드 내부에서만 동작합니다.
- **Narrowest Required Verification**:
  - `core/web_claims.py` 로직에 대한 신규 유닛 테스트 케이스 추가.
  - `e2e/tests/web-smoke.spec.mjs` (또는 유사한 browser smoke)에서 `claim-coverage panel`의 `actionable hints` 및 재조사 후 상태 전이 검증.

## 4. 기대 효과
- 내부 관리용 문서 수정을 넘어, 실질적인 브라우저 MVP의 품질을 한 단계 끌어올립니다.
- "Still unresolved" 또는 "Single-source" 슬롯에 대한 재조사 적중률을 높여 사용자 신뢰도를 개선합니다.
