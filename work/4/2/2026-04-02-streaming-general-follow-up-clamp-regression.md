# 2026-04-02 streaming general follow-up clamp regression

**범위**: `stream_answer_with_context(intent="general")` 경로의 metadata 필터 + 4문장 clamp가 최종 `text_replace` event까지 올바르게 적용되는지 전용 regression 1건 추가
**근거**: `verify/4/2/2026-04-02-general-follow-up-runtime-density-clamp-verification.md` — non-stream `answer_with_context` 경로는 이미 regression이 있으나 streaming 경로의 최종 `text_replace` clamp는 전용 regression 없이 남아 있었음

---

## 변경 파일

- `tests/test_ollama_adapter.py` — `test_stream_general_follow_up_clamps_via_text_replace` 1건 추가

---

## 사용 skill

- 없음

---

## 변경 이유

이전 라운드에서 `_postprocess_general`과 non-stream regression 2건을 추가하여 `general` follow-up의 runtime clamp를 닫았으나, streaming 경로(`stream_answer_with_context`)에서 `_postprocess_answer` → `text_replace` event를 통해 동일한 clamp가 최종 출력까지 반영되는지 확인하는 전용 regression이 없었음. 같은 family의 smallest current-risk reduction으로 이 공백을 잠금.

---

## 핵심 변경

1. `tests/test_ollama_adapter.py`에 `test_stream_general_follow_up_clamps_via_text_replace` 추가:
   - `_iter_generate_raw`를 mock하여 메타데이터성 첫 문장("작성일: 2026-04-01.") + 5문장 일반 답변을 2개 chunk로 스트리밍
   - `stream_answer_with_context(intent="general")`로 전체 event 수집
   - `_apply_stream_event`로 최종 누적 텍스트 추적
   - `text_replace` event가 1개 이상 발생했는지 확인
   - 최종 텍스트에서 메타데이터("작성일") 제거 확인
   - 최종 텍스트가 2~4문장인지 확인

---

## 검증

- `python3 -m py_compile model_adapter/ollama.py tests/test_ollama_adapter.py` — 통과
- `python3 -m unittest -v tests.test_ollama_adapter` — **29 tests OK** (기존 28 + 신규 1)

---

## 남은 리스크

- `model_adapter/ollama.py` 코드 변경 없음. 기존 `_postprocess_answer` → `_postprocess_general` 경로가 streaming에서도 올바르게 작동하는 것을 regression으로 확인한 것이므로 새 코드 리스크 없음.
- `general` follow-up의 non-stream + stream 양쪽 모두 전용 regression이 잠겼으므로 이 family의 current-risk는 닫힌 상태.
- 다음 슬라이스는 같은 family가 아닌 새 quality axis 또는 다른 current-risk reduction으로 넘어가야 함.
