# 2026-04-19 Claim Coverage Summary CONFLICT family polish arbitration

## 중재 배경
- seq 382까지 CONFLICT 상태가 모든 브라우저 표면(History, Bar, Live Session, Panel Hint) 및 문서에 정합하게 노출됨.
- 현재 CONFLICT family의 기능적 구현 및 가시성 확보는 완료되었으며, `GEMINI.md` 우선순위에 따라 "same-family user-visible improvement" 단계의 마지막 폴리싱을 진행할 시점임.
- `core/agent_loop.py`의 `_build_claim_coverage_progress_summary`는 focus slot이 해결되지 않았을 때 `{current_label} 상태입니다.`라는 범용 템플릿을 사용하고 있어, `CONFLICT` 상황에서도 "정보 상충 상태입니다."라는 다소 기계적인 문구가 출력됨.

## 결정 및 권고
- **RECOMMEND: implement Agent Loop CONFLICT-Specific Focus-Slot Wording — fixed template polish**
- **결정 이유**:
    - "Priority 2: same-family user-visible improvement" 원칙에 따라, 사용자에게 상충 상황을 더 명확하고 자연스럽게 전달하는 전용 문구 적용을 권고함.
    - Milestone 4의 새로운 axis(Priority 3)로 넘어가기 전, 현재 family의 "마지막 한 조각(polish)"을 정교하게 닫음으로써 기능의 완결성을 높임.
    - Gemini가 구체적인 문구 템플릿을 고정함으로써 설계 모호성을 제거하고 bounded slice로 구현 가능하게 함.

## 상세 가이드 (Option A 기반)
- **수정 대상 파일**:
    - `core/agent_loop.py`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/agent_loop.py`: `_build_claim_coverage_progress_summary`의 `unresolved_slots` 루프 내에 `CoverageStatus.CONFLICT` 전용 분기 추가.
    - **고정 템플릿**: `"재조사했지만 {slot}{focus_particle} 출처들이 서로 어긋난 채 남아 있습니다."`
    - 기존 `WEAK`나 `MISSING` 상태의 범용 템플릿(`아직 {current_label} 상태입니다.`)은 그대로 유지.
    - `tests/test_smoke.py`: `CONFLICT` 상태의 focus slot에 대해 위 새 문구가 정확히 출력되는지 확인하는 regression test case 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k coverage`
    - `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
    - `git diff --check`
