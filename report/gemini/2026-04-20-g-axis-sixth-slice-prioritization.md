# 2026-04-20 G-axis sixth slice prioritization

## 개요
- seq 453(G2-deferred-B)을 통해 Claim Coverage 지표 소비(Consumption) 매트릭스가 완결됨.
- 다음 단계로 지표의 정확성(Accuracy)을 담보하기 위한 G4 튜닝을 선정함.

## 판단
1. **same-family current-risk reduction (우선순위 1):**
   - 현재 `DATABASE` 출처가 `role_confidence` 맵에서 누락되어 신뢰 등급(`trust_tier`) 계산 시 저신뢰(0.4)로 처리되고 있음. 이는 앞선 라운드에서 UI에 노출하기 시작한 신뢰 등급 정보의 정확성을 직접적으로 해치는 리스크임.
   - `OFFICIAL`(rank 5)보다 `WIKI`(rank 4)의 confidence가 높게 설정된 불일치도 함께 교정하여 내부 정합성을 확보함.

2. **유지보수 부채(Maintenance Debt) 인지:**
   - 현재 `tests.test_web_app` 및 `SQLiteSessionStore` 관련 테스트 실패가 다수 존재함. 이는 G4 이후의 최우선 순위(G5/G6)로 다뤄져야 할 축임. 하지만 기능적 정합성(G4)을 먼저 맞추는 것이 "Same-family" 원칙에 부합함.

## 권고 (RECOMMEND)
- **G4: `_role_confidence_score` float-axis tuning**
- 구체적 범위:
  - `core/agent_loop.py::_build_entity_claim_records` 수정.
  - `role_confidence` 맵에 `SourceRole.DATABASE: 0.9` 추가.
  - `SourceRole.OFFICIAL`을 `0.95`로, `SourceRole.WIKI`를 `0.9`로 조정하여 우선순위 계층과 일치시킴.
  - `tests/test_smoke.py -k claims`를 통해 랭킹 및 `trust_tier` 변화 확인.

## 결론
G4를 통해 지표 데이터의 정확도를 확보하고, 다음 라운드부터는 누적된 테스트 실패를 해결하는 안정화 단계(G5/G6)로 진입할 것을 권고함.
