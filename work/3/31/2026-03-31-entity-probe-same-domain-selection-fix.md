# 2026-03-31 entity probe same-domain selection fix

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, entity-card missing-slot official probe가 same-domain hostname dedupe에 막히는 current-risk를 수정하도록 지시.
- 기존 `_push()`의 hostname dedupe가 무조건 같은 도메인을 차단하여, generic official overview가 먼저 선택된 뒤 같은 도메인의 slot-targeted probe 결과가 들어오면 probe가 탈락했음.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_push()` 함수에 probe 대체 로직 추가: probe_bonus > 0인 소스가 같은 도메인의 generic 소스(probe_bonus = 0)를 chosen에서 교체 가능
   - 교체된 generic 소스는 `evicted_source_ids`에 추가되어 3rd fallback pass에서 재추가 방지
   - generic 소스가 hostname dedupe로 차단될 때, 이미 같은 도메인에 probe 소스가 있으면 `evicted_source_ids`에도 추가
2. `evicted_source_ids` set 추가: evict된 소스와 probe 도메인 차단 소스를 추적
3. 3rd fallback pass에서 `evicted_source_ids` 체크 추가 (기존 `source in chosen` 외)
4. 3rd fallback pass의 기존 동작(같은 도메인 다른 페이지 허용)은 유지 — probe 대체가 아닌 일반적 same-domain case는 영향 없음

### 테스트 변경 (`tests/test_smoke.py`)
- `test_web_search_entity_probe_replaces_same_domain_generic_official` 추가
  - fixture: namu.wiki + pearlabyss.com generic overview(boardNo=100) + pearlabyss.com platform probe(boardNo=200)
  - probe 페이지에 "PC와 콘솔 플랫폼으로 출시 예정" 텍스트 포함
  - 검증: probe(boardNo=200)가 선택되고 generic(boardNo=100)은 탈락

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- latest_update/live threshold, source_policy 점수표 변경 없음
- 비entity 검색 경로의 3rd pass 동작 변경 없음

## 검증
- `python3 -m unittest -v tests.test_smoke`: 92 tests, OK (1.043s)
- `python3 -m unittest -v tests.test_web_app`: 110 tests, OK (1.806s)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`: 통과

## 남은 리스크
- probe 대체는 같은 도메인 내 probe_bonus > 0 vs probe_bonus = 0 충돌에서만 작동. 두 probe가 같은 도메인의 다른 슬롯을 메우는 경우는 현재 지원하지 않음 (첫 번째 probe만 유지).
- dirty worktree가 여전히 넓음.
