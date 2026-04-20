# 2026-04-19 Milestone 4 Source Role Weighting — NEWS elevation arbitration

## 중재 배경
- seq 388, 391, 394를 통해 `OFFICIAL(5)`, `WIKI(4)=DATABASE(4)`, `DESCRIPTIVE(3)` 계층이 확립됨.
- 현재 `NEWS` (보조 기사)와 `AUXILIARY` (보조 출처)가 동일하게 `1` 수준에 머물러 있어, 검증된 언론사 기사와 일반적인 보조 정보 간의 우선순위가 구분되지 않는 상태임.
- `Milestone 4`의 출처 가중치 축을 완결성 있게 닫기 위해, 이 두 역할 간의 위계를 정립할 필요가 있음.

## 결정 및 권고
- **RECOMMEND: implement Milestone 4 Source Role Weighting — NEWS elevation**
- **결정 이유**:
    - "Priority 3: new quality axis"의 세부 정교화 단계로, 언론사 기사(`NEWS`)와 일반 보조 정보(`AUXILIARY`) 간의 변별력을 확보함.
    - `NEWS` (보조 기사)는 언론사의 사실 확인을 거친 정보로, 단순 파편적 정보인 `AUXILIARY` (보조 출처)보다 높은 신뢰도를 가짐.
    - 따라서 `NEWS`의 우선순위를 `1`에서 `2`로 상향하여, `DESCRIPTIVE` (3)와 `AUXILIARY` (1) 사이의 완충 계층으로 배치함. 이로써 `Source Role Weighting` 계층 구조의 논리적 완결성을 높임.

## 상세 가이드 (Option A2 기반)
- **수정 대상 파일**:
    - `core/web_claims.py`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/web_claims.py`: `_ROLE_PRIORITY` 딕셔너리에서 `SourceRole.NEWS`의 값을 `1`에서 `2`로 상향 조정.
    - `AUXILIARY`는 `1`로 유지하여 `NEWS`가 이를 앞서게 함.
    - `tests/test_smoke.py`: `NEWS`와 `AUXILIARY` (1) 간의 tie-break에서 `NEWS`가 승리하는지, 그리고 `NEWS`가 여전히 `DESCRIPTIVE` (3)보다는 낮은 우선순위를 갖는지 확인하는 regression test case 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k claims`
    - `python3 -m py_compile core/web_claims.py tests/test_smoke.py`
    - `git diff --check`
