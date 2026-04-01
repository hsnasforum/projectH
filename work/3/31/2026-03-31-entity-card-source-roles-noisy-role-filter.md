# 2026-03-31 entity-card source_roles noisy role filter

## 변경 파일
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 같은 multi-source agreement / single-source noise family에서 `response_origin.source_roles`와 history badge에 noisy single-source role이 누출되는 user-visible 문제를 잠그도록 지시.
- 본문 텍스트에서는 noisy claim이 이미 억제되지만, badge/meta의 `source_roles`에 `'설명형 출처'`가 남아 있었음.

## 핵심 변경
- `_build_web_search_origin` 수정 (`core/agent_loop.py`)
  - `answer_mode == "entity_card"`일 때, fact bullet을 추출하지 못한 source를 `source_roles` 산출 대상에서 제외
  - fallback: 모든 source가 제외되면 원래 source 목록 유지
- `test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload` 확장 (`tests/test_web_app.py`)
  - 첫 응답: `source_roles == ['백과 기반']`, `'설명형 출처'` 미포함 assertion 추가
  - 첫 응답 history badge: `source_roles == ['백과 기반']` assertion 추가
  - 자연어 reload: `source_roles == ['백과 기반']`, `'설명형 출처'` 미포함 assertion 추가

## 검증
- `python3 -m unittest -v tests.test_web_app`: 124 tests, OK (2.390s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- `verification_label`은 여전히 `"설명형 다중 출처 합의"`로 남음 — 이는 source_type 기반 집계이고 role 기반이 아니므로 이번 scope에서 제외.
- multi-source agreement / single-source noise family: 본문 텍스트 + source_roles badge 모두 잠김. verification_label까지 포함하면 같은 family의 추가 slice가 남을 수 있음.
- dirty worktree가 여전히 넓음.
