# 2026-03-31 multi-source agreement over noise reload lock

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 이전 라운드 테스트에 noisy single-source source가 빠져 있어 "agreement over noise" slice가 truthfully 닫히지 않았다고 지적.
- same-family current-risk reduction: 기존 테스트 fixture에 noisy single-source source 1개를 추가하고, initial/reload 양쪽에서 noisy claim 미노출을 explicit assertion으로 잠그도록 보강.

## 핵심 변경
- `test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload` 수정 (`tests/test_web_app.py`)
  - fixture 변경: 기존 wiki 2개에 noisy blog source 1개 추가 (boilerplate 섞인 페이지 텍스트, "출시일"/"2025" 고유 claim)
  - 첫 응답 assertion 추가: `사실 카드:` + `교차 확인` 텍스트 존재, `출시일`/`2025` 미노출
  - reload assertion 추가: `사실 카드:` + `교차 확인` 유지, `출시일`/`2025` 미노출
  - strong slot 유지, weak/strong 비중첩 assertion 유지
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 123 tests, OK (2.174s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (이번 변경은 test fixture만 수정, browser-visible 변경 없음)

## 남은 리스크
- multi-source agreement / single-source noise family의 history-card reload path는 이제 truthfully 잠김 (agreement 유지 + noisy claim 미노출).
- natural reload 경로 ("방금 검색한 결과 다시 보여줘")의 agreement-over-noise retention은 아직 별도 테스트 없음 — 같은 family의 다음 slice 후보.
- dirty worktree가 여전히 넓음.
