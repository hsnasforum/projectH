# 2026-04-19 Milestone 4 Reinvestigation Wording Polish arbitration

## 중재 배경
- seq 385에서 `CONFLICT` ("정보 상충") 전용 포커스 슬롯 문구가 도입되어 가독성이 개선됨.
- 하지만 `WEAK` ("단일 출처")와 `MISSING` ("미확인") 슬롯은 여전히 `"아직 {label} 상태입니다"`라는 기계적인 범용 템플릿을 공유하고 있어, `reinvestigation` 축의 사용자 체감 품질이 상충 슬롯에 비해 떨어지는 상태임.
- CONFLICT family의 문서 동기화가 완료(seq 402)되었으므로, Milestone 4의 핵심 축 중 하나인 `Reinvestigation`의 품질을 보강하여 이 family를 더욱 견고하게 닫을 시점임.

## 결정 및 권고
- **RECOMMEND: implement Milestone 4 Strong vs Weak vs Unresolved Separation beyond CONFLICT (Option C)**
- **결정 이유**:
    - "Priority 2: same-family user-visible improvement" 원칙에 따라, 사용자에게 조사 진행 상황을 더욱 자연스럽고 명확하게 전달하는 전용 문구 분리를 권고함.
    - `CONFLICT` 워딩 폴리싱의 성공 사례를 `WEAK`와 `MISSING`으로 확장하여, 에이전트 루프의 전체적인 응답 품질 일관성을 확보함.
    - `Source Role Weighting` 계층은 현재 충분히 논리적으로 완결(`OFFICIAL > WIKI=DATABASE > DESCRIPTIVE > NEWS > AUXILIARY`)되어 있으므로, 추가적인 미세 조정(Option A)보다는 실제 사용자 노출 문구 개선(Option C)이 우선순위가 높음.

## 상세 가이드 (Option C 기반)
- **수정 대상 파일**:
    - `core/agent_loop.py`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/agent_loop.py`: `_build_claim_coverage_progress_summary`의 focus-slot unresolved 분기 수정.
    - **WEAK 템플릿**: `"재조사했지만 {slot}{focus_particle} 아직 한 가지 출처의 정보로만 확인됩니다."`
    - **MISSING 템플릿**: `"재조사했지만 {slot}{focus_particle} 아직 관련 정보를 찾지 못했습니다."`
    - `CONFLICT` 전용 문구와 기존 rank/label/probe 로직은 건드리지 않음.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k coverage` (신규 워딩 검증용)
    - `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
    - `git diff --check`
