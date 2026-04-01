# 2026-03-31 history-card reload badge Playwright smoke

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: needs_operator`로 멈춘 후, operator가 옵션 1(browser-visible current-risk reduction: history-card click 후 badge/label 유지 Playwright smoke 1건)을 선택.
- 기존 smoke(`web-search history card header badges`)는 `renderSearchHistory`로 badge 렌더링만 검증하고, 실제 card 클릭 → 서버 reload → badge 유지를 확인하지 않음.
- history-card "다시 불러오기" 클릭이 `loadWebSearchRecord(record_id)` → `/api/chat`(load_web_search_record_id) 경로를 거쳐 올바른 badge를 표시하는지가 browser-visible contract의 유일한 미검증 경로였음.

## 핵심 변경
- `history-card 다시 불러오기 클릭 후 response origin badge와 answer-mode badge가 유지됩니다` smoke 추가 (`e2e/tests/web-smoke.spec.mjs`)
  - pre-seeded record: entity-card fixture(namu.wiki 붉은사막)를 `data/web-search/<session_id>/` 에 JSON 파일로 직접 생성하여 네트워크 의존 없이 테스트
  - `renderSearchHistory`로 history card를 렌더링한 뒤 "다시 불러오기" 클릭
  - 서버가 저장된 record를 reload하여 entity_card response_origin을 계산
  - exact assertion:
    - `#response-origin-badge`: text "WEB", class `web`
    - `#response-answer-mode-badge`: visible, text "설명 카드"
    - `#response-origin-detail`: "설명형 단일 출처" 포함, "백과 기반" 포함
  - best-effort cleanup으로 pre-seeded 파일 제거
- production 코드 변경 없음 — smoke-only slice
- docs, approval flow, reviewed-memory 변경 없음

## 검증
- `make e2e-test`: 16 tests passed (4.2m), 새 테스트 8.2s에 통과
- `python3 -m unittest -v tests.test_web_app`: 106 tests, OK (1.777s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py e2e/tests/web-smoke.spec.mjs`: 통과

## 남은 리스크
- pre-seeded record의 entity_card 판정은 `_reuse_web_search_record`에서 `claim_coverage`가 non-empty일 때 결정됨. namu.wiki snippet으로 entity claim이 생성되지 않는 edge case가 있으면 answer_mode가 "general"로 떨어질 수 있음 — 현재 fixture에서는 entity claim이 생성되어 통과.
- best-effort cleanup이 실패하면 `data/web-search/` 아래에 test 잔여 파일이 남을 수 있음.
- dirty worktree가 여전히 넓음.
