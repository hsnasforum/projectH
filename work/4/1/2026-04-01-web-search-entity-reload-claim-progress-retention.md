# 2026-04-01 web search entity reload claim progress retention

## 변경 파일
- `storage/web_search_store.py`
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, entity-card history reload에서 `claim_coverage_progress_summary` 보존을 지시.
- 기존 코드는 `claim_coverage`는 저장하지만 `claim_coverage_progress_summary`는 저장하지 않아, history-card reload 시 slot progress 요약이 사라지거나 drift하는 user-visible evidence continuity 문제.

## 핵심 변경
- `storage/web_search_store.py`
  - `save()` 메서드에 `claim_coverage_progress_summary: str | None` 파라미터 추가
  - record JSON에 `claim_coverage_progress_summary` 필드 저장
- `core/agent_loop.py`
  - `save()` 호출 시 `claim_coverage_progress_summary` 전달
  - `_reuse_web_search_record()`에서 stored `claim_coverage`가 있으면 재계산 대신 복원
  - stored `claim_coverage_progress_summary`도 함께 복원
  - stored claim context가 없을 때만 기존 재계산 fallback 유지
  - reload 시 `_build_web_search_active_context()`에 `claim_coverage_progress_summary` 전달
- `tests/test_web_app.py`
  - `test_handle_chat_entity_card_reload_preserves_claim_coverage_progress_summary` 추가
  - entity search → load_web_search_record_id reload에서 claim_coverage slots와 progress_summary가 그대로 보존되는지 확인

## 검증
- `python3 -m unittest -v tests.test_web_app`: 180 tests, OK (3.132s)
- `git diff --check -- storage/web_search_store.py core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- `latest_update` / `general` path의 reload evidence continuity는 이번 라운드 범위 밖.
- dirty worktree가 여전히 넓음.
