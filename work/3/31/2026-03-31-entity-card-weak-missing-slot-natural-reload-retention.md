# 2026-03-31 entity-card weak/missing slot natural reload retention

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, entity-card의 weak/missing slot 섹션 분리가 자연어 recent-record reload 후에도 유지되는지 확인하도록 지시.
- 이전 라운드에서 history-card reload 경로의 production fix(stored intent_kind/answer_mode 전달)가 자연어 reload에도 동일하게 적용되는지 확인 필요.

## 핵심 변경
- `test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_natural_reload` 추가 (`tests/test_web_app.py`)
  - 첫 호출: namu.wiki 단일 소스 entity search
  - 둘째 호출: `"방금 검색한 결과 다시 보여줘"` 자연어 reload
  - 검증: `불확실 정보:` + `추가 확인 필요:` 섹션 분리, `단일 출처` / `교차 확인 가능한 근거가 더 필요합니다` 문구, claim_coverage에 weak + missing 모두 존재
- production 코드 변경 없음 — test-only slice (이전 라운드 fix가 자연어 reload에도 작동 확인)

## 검증
- `python3 -m unittest -v tests.test_web_app`: 122 tests, OK (2.213s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음

## 남은 리스크
- entity-card weak/missing slot section separation family는 initial response + history-card reload + natural reload 3개 경로를 모두 explicit regression으로 잠금. 이 family는 닫힘.
- dirty worktree가 여전히 넓음.
