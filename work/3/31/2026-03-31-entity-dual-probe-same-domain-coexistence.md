# 2026-03-31 entity dual-probe same-domain coexistence

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 같은 official domain의 probe 두 개가 서로 다른 missing slot을 메울 때 첫 번째 probe만 유지되는 current-risk를 수정하도록 지시.
- 이전 라운드에서 probe가 generic official을 대체하는 로직은 추가했으나, probe끼리의 same-domain 공존은 지원하지 않았음.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_push()` 함수의 same-domain probe 충돌 처리에 slot 비교 분기 추가:
   - 기존: same-domain에 probe가 이미 있으면 → `return False` (무조건 차단)
   - 변경: 새 probe의 target slot이 기존 probe의 target slot과 다르면 → `pass` (공존 허용)
   - `_entity_slot_from_search_query`로 각 probe의 `matched_query`에서 target slot 추출
   - 같은 slot이면 여전히 차단 (중복 probe 방지)

### 테스트 변경 (`tests/test_smoke.py`)
- `test_web_search_entity_dual_probe_different_slots_coexist_on_same_domain` 추가
  - fixture: namu.wiki + pearlabyss.com platform probe(boardNo=200, 이용 형태) + pearlabyss.com service probe(boardNo=300, 서비스/배급)
  - 검증: `selected_source_paths`에 두 probe URL이 모두 포함
  - entity claims selection 경로(max_items=3)에서 두 probe가 공존하여 missing slot 2개를 동시에 보강

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- generic official vs probe 대체 로직(이전 라운드) 유지
- `_build_web_search_active_context`의 별도 `_select_ranked_web_sources(max_items=5)` 호출 경로는 변경하지 않음

## 검증
- `python3 -m unittest -v tests.test_smoke`: 93 tests, OK (1.030s)
- `python3 -m unittest -v tests.test_web_app`: 110 tests, OK (1.714s)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`: 통과

## 남은 리스크
- `_build_web_search_active_context`의 독립적 `_select_ranked_web_sources` 호출에서는 dual-probe 공존이 반영되지 않을 수 있음. entity claims selection(핵심 경로)에서는 작동 확인됨.
- 같은 slot을 타겟하는 same-domain probe 2개는 여전히 첫 번째만 유지됨 (의도된 동작).
- dirty worktree가 여전히 넓음.
