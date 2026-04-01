# 2026-03-31 entity-card trust-weighted agreement

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 entity-card quality 개선 → 옵션 A(다중 출처 합의 신뢰도 개선: peer trust 가중 agreement score)를 선택.
- 기존 `_entity_source_fact_agreement_score`는 모든 peer 합의에 동일 가중치(+4)를 부여하여, 블로그 2개 합의와 위키+공식 합의가 같은 점수를 받았음.
- 이로 인해 소스 선택 시 신뢰할 수 있는 peer와의 합의가 충분히 반영되지 않았음.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_entity_source_fact_agreement_score`에 `trust_score_by_index` 파라미터 추가 (optional, 기본값 None으로 하위 호환)
2. 내부 자료구조를 `support_by_label: dict[str, int]`에서 `peers_by_label: dict[str, list[int]]`로 변경하여 어떤 peer가 합의했는지 추적
3. 각 합의 label에 대해 best peer trust >= 7이면 추가 +2 보너스
   - wiki(trust 12), official(trust 10), database(trust 9): 보너스 대상
   - news(trust 1), general(trust 4~7), community(trust -5): 보너스 없음
4. `_select_ranked_web_sources`에서 `trust_score_by_index` dict를 미리 계산하여 agreement 함수에 전달

### 테스트 변경 (`tests/test_smoke.py`)
- `test_web_search_entity_agreement_prefers_trusted_peer_over_low_trust_peer` 추가
  - fixture: wiki(namu.wiki) + community(inven.co.kr) + official(pearlabyss.com)
  - 모두 "붉은사막은 펄어비스가 개발" 사실에 합의
  - 검증: wiki와 official이 선택되고, community는 선택되지 않음
  - trust-weighted agreement에 의해 wiki+official 조합이 wiki+community보다 우선됨

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- 기존 base agreement 점수(+4 per label, +2 for 2+ peers, +1 for core slot, +3 for 2+ labels) 변경 없음
- source_policy.py의 trust score 체계 변경 없음

## 검증
- `python3 -m unittest -v tests.test_smoke`: 89 tests, OK (0.954s)
- `python3 -m unittest -v tests.test_web_app`: 106 tests, OK (1.845s)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`: 통과

## 남은 리스크
- trust 보너스 threshold(>= 7)은 현재 entity_score 분포 기준으로 설정됨. source_policy.py의 점수 체계가 변경되면 threshold 재검토 필요.
- trust_score_by_index를 전달하지 않는 기존 호출자(None 기본값)에서는 trust 가중이 적용되지 않음. 현재는 `_select_ranked_web_sources` 내부에서만 호출하므로 문제 없음.
- dirty worktree가 여전히 넓음.
