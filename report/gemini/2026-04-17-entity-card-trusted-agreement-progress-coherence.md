# 2026-04-17 entity-card trusted-agreement progress coherence

## 분석

`work/4/17/2026-04-17-entity-card-trusted-agreement-conflict-sensitive-claim-coverage.md`를 통해 `core/web_claims.py`의 `summarize_slot_coverage()` 로직이 신뢰할 만한 출처($\ge 2$)와 상충 의견 부재를 요구하도록 엄격해졌습니다. `verify` 라운드 결과, 해당 로직의 구현과 핵심 회귀 테스트는 통과하였으나 `tests.test_web_app` 전체 suite에서 발생하는 `PermissionError`(socket bind)는 이번 로직 변경과는 무관한 환경적 요인으로 확인되었습니다.

현재 `core/agent_loop.py`의 `_annotate_claim_coverage_progress` 및 `_build_claim_coverage_progress_summary`는 단순히 상태 랭크의 변화(STRONG/WEAK/MISSING)만 보고 "보강됨", "약해짐"과 같은 일반적인 문구만 생성하고 있습니다. 이는 백엔드에서 구현된 "신뢰 출처 간의 합의" 또는 "신뢰 출처 간의 충돌로 인한 강등"이라는 구체적인 품질 개선 사항을 사용자에게 자연어 문맥으로 충분히 전달하지 못하는 상태입니다.

## 조언

`browser-investigation` 패밀리의 품질 축(Quality Axis)을 완성하기 위해, 엄격해진 신뢰 합의 로직에 걸맞은 **한국어 진행 요약 고도화(Natural Korean Progress Summary)** 슬라이스를 추천합니다.

1.  **우선순위 판단**:
    *   `web_claims.py`의 엄격한 로직과 `agent_loop.py`의 단순한 진행 요약 사이의 의미적 괴리(Drift)를 해소하는 것은 "same-family current-risk reduction"이자 "user-visible improvement"에 해당합니다.
    *   `gemini_request.md`의 지침에 따라 환경적 요인인 `PermissionError` 수정보다는 제품 가치에 직결된 품질 개선을 우선합니다.

2.  **구체적 구현 방향**:
    *   `core/agent_loop.py`의 진행 요약 생성 로직에서 단순히 랭크 변화만 보는 것이 아니라, `web_claims.py`의 `has_conflict` 여부 등을 인지하여 더 구체적인 한국어 설명을 생성합니다.
    *   예: `CoverageStatus.STRONG`에서 `WEAK`로 강등된 경우, 단순 "약해짐" 대신 "신뢰할 만한 다른 의견이 관찰되어 교차 확인에서 제외되었습니다"와 같은 구체적인 설명을 포함하고 조사가 자연스럽게 연결되도록 처리합니다.

## 추천 슬라이스

`RECOMMEND: implement natural Korean progress summary refinement for trusted-agreement transitions in core/agent_loop.py`

*   `core/agent_loop.py` 내의 `_build_claim_coverage_progress_summary` 및 관련 헬퍼를 수정하여 `web_claims.py`의 새로운 신뢰 합의/상충 로직에 특화된 상세 한국어 설명(Explanation)과 자연스러운 조사 처리를 구현하는 슬라이스입니다.
*   이미 통과된 `core/web_claims.py`의 엄격한 판정 로직을 UI/History 메타데이터의 자연어 설명 축과 동기화하여 제품의 신뢰도 체감을 완성합니다.
