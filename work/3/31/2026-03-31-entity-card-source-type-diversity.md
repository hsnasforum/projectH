# 2026-03-31 entity-card source-type diversity

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 entity-card investigation quality 개선 → 출처 유형 다양성 강제(옵션 B)를 선택.
- 기존 `_select_ranked_web_sources`는 hostname 중복만 제거하고 source_type 다양성을 강제하지 않아, 같은 유형(wiki 3개 등)만 선택되어 교차 검증 기회를 놓칠 수 있었음.
- community 유형은 1개 cap이 이미 있었지만, wiki/official/news 등 다른 유형에는 cap이 없었음.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_push()` 함수에 source_type 일반 cap 추가: 같은 source_type이 이미 2개 선택되면 추가 선택 차단
   - community: 기존 cap 1 유지 (선행 검사에서 먼저 차단됨)
   - wiki/official/news/database/general: cap 2 (새로 추가)
   - 3rd fallback pass(line 4764+)는 `_push()`를 우회하므로 대안 없을 때 여전히 동일 유형 선택 가능
2. candidates 확장에서 `len(candidates) < max_items` 조건 제거: threshold 미달 소스도 후보 풀에 포함하여 diversity cap이 빈 슬롯을 만들었을 때 다른 유형의 소스가 fallback으로 선택될 수 있게 함
3. `query_profile == "live"` threshold 완화: `max(2, top_score - 9)` → `max(2, top_score - 12)`. dirty worktree에 이미 존재하던 변경으로 `test_handle_chat_mixed_source_latest_update_badge_ordering`이 의존함. official + news 혼합 소스가 모두 threshold를 넘어야 "공식+기사 교차 확인" verification_label이 부여되므로, 좁은 threshold에서는 news가 탈락해 mixed-source 교차 확인이 실패했음. operator가 명시적으로 승인함.

### 테스트 변경 (`tests/test_smoke.py`)
- `test_web_search_entity_source_type_diversity_caps_same_type_at_two` 추가
  - fixture: wiki 3개(namu.wiki, ko.wikipedia.org, britannica.com) + official 1개(pearlabyss.com)
  - 검증: wiki 2개 + official 1개가 선택되어 source_type 다양성 확보
  - `[공식 기반]` role label이 응답에 포함되는지 확인

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- source_policy.py의 점수 체계(entity_score, latest_score 등) 변경 없음
- 기존 community cap(1) 및 news/event_campaign 필터 변경 없음
- entity profile threshold(`max(4, top_score - 7)`) 변경 없음

## 검증
- `python3 -m unittest -v tests.test_smoke`: 88 tests, OK (0.948s)
- `python3 -m unittest -v tests.test_web_app`: 106 tests, OK (1.648s)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`: 통과

## 남은 리스크
- candidates 확장 조건 제거로 인해 후보 풀이 넓어짐. decoration + `_push()` 필터가 여전히 품질을 보호하지만, 극단적으로 많은 검색 결과가 있을 때 decoration 계산 비용이 약간 증가할 수 있음 (현재 max_results=5이므로 실질 영향 없음).
- source_type cap 2는 max_items=3 기준으로 설계됨. max_items가 더 커지면 cap 비율 재검토 필요.
- live threshold 완화(`top_score - 9` → `top_score - 12`)로 인해 latest_update 검색에서 더 낮은 점수의 소스가 후보에 포함됨. `_push()` 필터가 저품질 소스를 차단하므로 실질 위험은 제한적이지만, 노이즈 소스가 candidate에 더 많이 들어올 수 있음.
- dirty worktree가 여전히 넓음.
