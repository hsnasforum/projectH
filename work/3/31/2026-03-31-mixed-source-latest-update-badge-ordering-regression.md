# 2026-03-31 mixed-source latest_update badge ordering regression + threshold fix

## 변경 파일
- `tests/test_web_app.py`
- `core/agent_loop.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `handle_chat → session.web_search_history` 경로에서 official-domain + news-domain mixed-source `latest_update` 결과의 `verification_label`, `source_roles` exact field ordering을 직접 assert하는 integration regression 1개 추가를 지시.
- 테스트 작성 중 실제 버그 발견: `_select_ranked_web_sources`의 `live` profile threshold(`top_score - 9`)가 너무 타이트하여, news 도메인이 높은 점수를 받을 경우 official 도메인이 threshold 미만으로 떨어져 `selected_sources`에서 제외됨. 이로 인해 `_build_web_verification_label`에서 `official_count >= 1 and news_count >= 1` 조건이 충족되지 않아 "공식+기사 교차 확인" label이 절대 나올 수 없는 상태였음.

## 핵심 변경
1. `test_handle_chat_mixed_source_latest_update_badge_ordering` 추가 (`tests/test_web_app.py`)
   - `_FakeWebSearchTool`에 official-domain(`store.steampowered.com`) 1건 + news-domain(`news.example.com`) 1건 fixture 구성
   - `handle_chat()` → `session.web_search_history[0]`에서:
     - `answer_mode == "latest_update"`
     - `verification_label == "공식+기사 교차 확인"`
     - `source_roles == ["보조 기사", "공식 기반"]` (score rank order)
2. `_select_ranked_web_sources` threshold 수정 (`core/agent_loop.py:4616`)
   - `live` profile threshold를 `top_score - 9` → `top_score - 12`로 완화
   - official 도메인이 news 도메인보다 term-matching 점수가 낮을 때도 cross-verification에 참여할 수 있게 함
   - entity(-7), general(-8) 대비 live(-12)가 넓지만, latest_update는 cross-verification 다양성이 중요하므로 적절한 범위

## 검증
- `python3 -m unittest -v tests.test_web_app`: 101 tests, OK (1.605s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`: 통과

## 남은 리스크
- `live` profile threshold 완화로 낮은 품질의 source가 포함될 가능성이 미미하게 증가. 다만 max_items=3 제한이 여전히 적용됨.
- source_roles ordering은 score rank 순서이므로 official이 항상 첫 번째가 아님. "공식+기사 교차 확인" label 자체는 ordering과 무관하게 type 카운트 기반으로 결정됨.
- dirty worktree가 여전히 넓음.
