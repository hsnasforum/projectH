# 2026-03-31 latest-update noisy source filtering

## 변경 파일
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 `multi-source agreement / single-source noise` family를 닫고 새 quality axis로 `B: latest_update answer-mode noise filtering`을 선택.
- latest_update 검색에서 noisy source가 본문·badge·source_roles에 혼입되지 않는지 같은 family의 current-risk 1건 잠금.

## 핵심 변경
- `_build_web_search_origin` defense-in-depth fix (`core/agent_loop.py`)
  - `answer_mode == "latest_update"`일 때 summary_text/snippet이 noisy인 source를 `source_roles` 산출 대상에서 제외
  - fallback: 모든 source가 제외되면 원래 source 목록 유지
- `_build_latest_update_web_summary` defense-in-depth fix (`core/agent_loop.py`)
  - 본문 텍스트 내 `출처 성격:` 줄 산출에도 동일한 noisy source 필터 적용
- `test_handle_chat_latest_update_noisy_source_excluded_from_body_and_badge` 추가 (`tests/test_web_app.py`)
  - fixture: 뉴스 2개 + noisy community source 1개 (brunch.co.kr, boilerplate snippet)
  - 첫 호출: latest_update 모드 확인, `보조 커뮤니티` role 미노출, `brunch` URL 본문 미노출
  - history badge: noisy role 미포함
  - 자연어 reload: noisy role/URL 미노출
- 참고: 현재 ranking이 noisy source를 이미 low-score로 제외하므로 production fix는 defense-in-depth 성격

## 검증
- `python3 -m unittest -v tests.test_web_app`: 125 tests, OK (2.377s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- latest_update noisy source filtering family의 첫 regression lock 완료.
- history-card `load_web_search_record_id` reload 경로에서도 latest_update noisy 필터가 동작하는지는 별도 테스트 없음 — 같은 family 다음 slice 후보.
- dirty worktree가 여전히 넓음.
