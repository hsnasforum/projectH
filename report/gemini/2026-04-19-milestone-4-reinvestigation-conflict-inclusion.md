# 2026-04-19 Milestone 4 Reinvestigation — CONFLICT inclusion arbitration

## 중재 배경
- seq 388~397을 통해 `Source Role Weighting` 계층이 `OFFICIAL(5) > WIKI/DATABASE(4) > DESCRIPTIVE(3) > NEWS(2) > AUXILIARY(1) > COMMUNITY/PORTAL/BLOG(0)`으로 정교화됨.
- `CONFLICT` ("정보 상충") family는 브라우저 표면 노출까지 완료되었으나, 서버 측의 "재조사 추천(reinvestigation suggestions)" 로직에서 여전히 `CONFLICT` 상태가 누락되어 있음을 확인.
- 현재 `core/agent_loop.py::_build_entity_reinvestigation_suggestions`는 `MISSING`과 `WEAK` 상태만 추천 후보로 고려하며, `CONFLICT` 슬롯은 추천 프롬프트 생성 대상에서 제외됨.

## 결정 및 권고
- **RECOMMEND: implement Milestone 4 Reinvestigation — CONFLICT inclusion in suggestions and probe limits**
- **결정 이유**:
    - `CONFLICT` family를 "shipped"로 선언했음에도 불구하고, 사용자가 상충된 정보를 해결하기 위해 "다시 검색해봐" 프롬프트를 받는 경로가 막혀 있는 것은 실질적인 기능적 결함(current-risk/gap)임.
    - Milestone 4의 `Reinvestigation` sub-axis로 전환하면서, `CONFLICT` 상태를 추천 로직 및 프로브 쿼리 제한 로직에 통합하여 family 간 정합성을 완성함.
    - `Source Role Weighting` 축은 이미 충분히 세분화되었으므로, 제품의 핵심 루프인 "조사-상충-재조사" 흐름을 닫는 쪽을 우선순위로 함.

## 상세 가이드 (Option B 기반)
- **수정 대상 파일**:
    - `core/agent_loop.py`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/agent_loop.py`: 
        1. `_build_entity_reinvestigation_suggestions`의 `status_priority`에 `CoverageStatus.CONFLICT: 2` 추가. (우선순위: MISSING(0) > WEAK(1) > CONFLICT(2))
        2. `max_queries_for_slot` 결정 로직에 `CONFLICT` 포함. 상충 해결을 위해 `CONFLICT` 상태에서도 `max_queries_for_slot = 2`를 허용하도록 확장.
    - `tests/test_smoke.py`: `CONFLICT` 슬롯이 재조사 추천 목록에 포함되는지, 그리고 프로브 쿼리 제한이 2개로 상향되는지 확인하는 regression test case 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k coverage`
    - `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
    - `git diff --check`
