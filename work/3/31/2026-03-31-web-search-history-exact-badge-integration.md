# 2026-03-31 handle_chat → web_search_history exact badge field integration regression 

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `handle_chat → session.web_search_history` 경로에서 `verification_label`과 `source_roles`의 exact field truth를 직접 assert하는 focused integration regression 1개 추가를 지시.
- 기존 store-level test(`test_web_search_store_badge_data_contract_serializes_exact_fields`)는 `WebSearchStore` 직접 호출만 보호하고, `handle_chat` → investigation pipeline → store → `_serialize_web_search_history` 전체 경로의 exact field 보존은 미보호 상태였음.
- 근거: `work/3/31/2026-03-31-web-search-badge-data-contract-regression.md`, `verify/3/31/2026-03-31-web-search-badge-data-contract-regression-verification.md`

## 핵심 변경
- `test_handle_chat_web_search_history_exact_badge_fields` 추가
  - `latest_update` 1건: `handle_chat`으로 "서울 날씨 검색해봐" 실행 후 `session.web_search_history[0]`에서:
    - `answer_mode == "latest_update"`
    - `verification_label == "단일 출처 참고"`
    - `source_roles == ["보조 출처"]`
  - `entity_card` 1건: `handle_chat`으로 "붉은사막에 대해 알려줘" 실행 후 `session.web_search_history[0]`에서:
    - `answer_mode == "entity_card"`
    - `verification_label == "설명형 단일 출처"`
    - `source_roles == ["백과 기반"]`
- UI, Playwright smoke, docs, approval flow, reviewed-memory 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 100 tests, OK (1.801s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`: 통과

## 남은 리스크
- 이 테스트는 mock provider + 단일 검색 결과 fixture 기준. 복수 source가 섞인 경우의 source_roles ordering은 별도 테스트 필요.
- dirty worktree가 여전히 넓음.
