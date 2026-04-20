# 2026-04-19 Claim Coverage CONFLICT family closure and Milestone 4 pivot arbitration

## 중재 배경
- seq 385를 통해 `core/agent_loop.py`의 focus-slot 전용 문구(Korean template)까지 적용됨으로써, `CONFLICT` ("정보 상충") family의 기능 구현, 브라우저 노출, 워딩 폴리싱, 문서 동기화가 모두 완료됨.
- `GEMINI.md`의 우선순위에 따라 current-risk reduction 및 same-family improvement가 모두 달성되었으므로, 이제 새로운 quality axis인 Milestone 4로의 전환(Priority 3)이 필요한 시점임.

## 결정 및 권고
- **RECOMMEND: implement Milestone 4 Source Role Weighting — official source elevation**
- **결정 이유**:
    - "Priority 3: new quality axis" 원칙에 따라, Milestone 4의 핵심 축 중 하나인 `Source Role Labeling / Weighting`으로의 피벗을 권고함.
    - 현재 `core/web_claims.py`의 `_ROLE_PRIORITY`는 `WIKI`(4)가 `OFFICIAL`(3)보다 높게 설정되어 있어, 지지 출처 수가 같을 경우 공식 소스보다 위키의 데이터가 우선 채택되는 품질 문제가 있음.
    - 게임의 개발사, 서비스 상태 등 엔티티 속성에 대해서는 공식 출처(OFFICIAL)를 최우선 권위로 설정하는 것이 "truthful grounded brief" 원칙에 부합함.

## 상세 가이드 (Option B 기반)
- **수정 대상 파일**:
    - `core/web_claims.py`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/web_claims.py`: `_ROLE_PRIORITY` 딕셔너리에서 `SourceRole.OFFICIAL`의 가중치를 `3`에서 `5`로 상향 조정하여 모든 출처 중 가장 높은 우선순위를 갖게 함.
    - `tests/test_smoke.py`: `WIKI`와 `OFFICIAL` 출처가 동일한 지지 수(support_count)를 가질 때, `OFFICIAL` 출처의 값이 최종적으로 선택되는지 확인하는 regression test case 추가.
    - `CONFLICT` family의 기존 구현 및 문서는 untouched 상태를 유지.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k claims`
    - `python3 -m py_compile core/web_claims.py tests/test_smoke.py`
    - `git diff --check`
