# 2026-04-19 Milestone 4 Source Role Weighting — DESCRIPTIVE elevation arbitration

## 중재 배경
- seq 391에서 `SourceRole.DATABASE` (데이터 기반)가 `4`로 승격되어 `WIKI`와 동등한 계층으로 정렬됨.
- `Milestone 4`의 `Source Role Weighting` 축을 지속하기 위해, 뉴스나 블로그보다는 권위 있지만 위키/데이터베이스보다는 보조적인 역할을 수행하는 `SourceRole.DESCRIPTIVE` (설명형 출처)의 위치를 조정할 필요가 있음.
- 현재 `DESCRIPTIVE`는 우선순위 `2`로, 뉴스(1)와 한 단계 차이이며 상위 계층(4)과는 두 단계 차이가 나는 상태임.

## 결정 및 권고
- **RECOMMEND: implement Milestone 4 Source Role Weighting — DESCRIPTIVE elevation**
- **결정 이유**:
    - "Priority 3: new quality axis" 원칙에 따라 출처 가중치 계층을 지속적으로 고도화함.
    - `SourceRole.DESCRIPTIVE` (심층 리뷰, 공식 가이드, 에디토리얼 페이지 등)는 단순 단신이나 파편화된 정보를 제공하는 `NEWS` (보조 기사)보다 구조화되고 권위 있는 정보를 제공함.
    - 따라서 `DESCRIPTIVE`의 우선순위를 `2`에서 `3`으로 상향하여, `NEWS/AUXILIARY` (1)와는 명확한 격차를 두고 상위 팩트 집계 계층(`WIKI/DATABASE`, 4)의 바로 아래 단계로 배치함.

## 상세 가이드 (Option A2 기반)
- **수정 대상 파일**:
    - `core/web_claims.py`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/web_claims.py`: `_ROLE_PRIORITY` 딕셔너리에서 `SourceRole.DESCRIPTIVE`의 값을 `2`에서 `3`으로 상향 조정.
    - 다른 역할들의 우선순위는 seq 391 상태 그대로 유지.
    - `tests/test_smoke.py`: `DESCRIPTIVE`와 `NEWS` (1) 간의 tie-break에서 `DESCRIPTIVE`가 승리하는지, 그리고 `DESCRIPTIVE`가 여전히 `DATABASE` (4)보다는 낮은 우선순위를 갖는지 확인하는 regression test case 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k claims`
    - `python3 -m py_compile core/web_claims.py tests/test_smoke.py`
    - `git diff --check`
