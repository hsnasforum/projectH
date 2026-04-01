# 2026-03-31 multi-source agreement reload retention

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, multi-source agreement / single-source noise 축에서 entity-card의 agreement-backed summary text가 `load_web_search_record_id` reload 후에도 유지되고 single-source noisy claim이 다시 노출되지 않는지 `tests/test_web_app.py` 1건으로 잠그도록 지시.
- operator가 다음 축으로 "A: multi-source agreement / single-source noise"를 선택함.

## 핵심 변경
- `test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload` 추가 (`tests/test_web_app.py`)
  - fixture: 나무위키 + 위키백과 2개 wiki 소스 (동일 snippet → agreement, support_count ≥ 2)
  - 첫 호출: entity-card 검색 → strong slot 최소 1개 확인
  - 둘째 호출: `load_web_search_record_id` reload
  - 검증: reload 후에도 strong slot이 유지, 사실 카드 섹션 유지, weak/missing slot이 strong slot과 겹치지 않음
- production 코드 변경 없음 — test-only slice (기존 reload path가 agreement filtering을 올바르게 보존하는지 확인)

## 검증
- `python3 -m unittest -v tests.test_web_app`: 123 tests, OK (2.340s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음

## 남은 리스크
- multi-source agreement family의 첫 regression lock. initial response + reload 경로를 잠금.
- natural reload 경로 ("방금 검색한 결과 다시 보여줘")의 agreement retention은 아직 별도 테스트 없음 — 같은 family의 다음 slice 후보.
- dirty worktree가 여전히 넓음.
