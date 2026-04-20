# 2026-04-19 Milestone 4 Source Role Weighting - DATABASE elevation arbitration

## 중재 배경
- seq 388에서 `SourceRole.OFFICIAL` (공식 기반)의 우선순위가 `5`로 승격되어 `WIKI` (4)를 앞서게 됨.
- `Milestone 4`의 `Source Role Weighting` 축을 지속하기 위해, 다음으로 권위 있는 출처인 `SourceRole.DATABASE` (데이터 기반)의 위치를 조정할 필요가 있음.
- 현재 `DATABASE`는 우선순위 `3`으로, 뉴스(1)나 설명형(2)보다는 높지만 위키(4)보다는 낮게 설정되어 있음.

## 결정 및 권고
- **RECOMMEND: implement Milestone 4 Source Role Weighting — DATABASE elevation to tie with WIKI**
- **결정 이유**:
    - "Priority 3: new quality axis" 원칙에 따라 출처 가중치 계층을 더욱 정교화함.
    - `SourceRole.DATABASE` (SteamDB, 퍼블리셔 데이터 페이지 등)는 단순 요약인 `WIKI`와 동등하거나 더 구체적인 팩트 기반 정보를 제공하는 경우가 많음.
    - 따라서 `DATABASE`의 우선순위를 `4`로 상향하여 `WIKI`와 동등한 "신뢰할 만한 팩트 출처" 계층으로 배치함. 이를 통해 지지 수가 같을 때 데이터 기반 정보가 2차 요약인 위키 정보에 밀리지 않도록 함.

## 상세 가이드 (Option A2 기반)
- **수정 대상 파일**:
    - `core/web_claims.py`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/web_claims.py`: `_ROLE_PRIORITY` 딕셔너리에서 `SourceRole.DATABASE`의 값을 `3`에서 `4`로 상향 조정.
    - `SourceRole.WIKI`는 `4`로 유지하여 두 역할이 우선순위 계층에서 동일한 위치를 갖게 함.
    - `tests/test_smoke.py`: `DATABASE`와 `DESCRIPTIVE` (2) 간의 tie-break에서 `DATABASE`가 승리하는지, 그리고 `DATABASE`와 `WIKI`가 동일한 우선순위를 갖는지 확인하는 regression test case 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k claims`
    - `python3 -m py_compile core/web_claims.py tests/test_smoke.py`
    - `git diff --check`
