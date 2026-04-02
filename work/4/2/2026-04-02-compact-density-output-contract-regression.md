# 2026-04-02 compact density output contract regression

**범위**: test-only — compact follow-up output contract의 밀도 범위를 regression으로 잠금
**근거**: `verify/4/2/2026-04-02-follow-up-answer-shape-consistency-verification.md` — compact output contract regression 부재

---

## 변경 파일

- `tests/test_ollama_adapter.py` — `test_compact_follow_up_intent_prompts_specify_density_bounds`에 output contract assertion 3건 추가

---

## 사용 skill

- 없음

---

## 변경 이유

이전 라운드에서 compact system prompt의 밀도 범위는 검증했으나 `_compact_intent_output_contract()`의 `action_items` (2~5개), `memo` (2~3개, 1~3개), `general` (2~4문장)은 regression으로 잠기지 않았음.

---

## 핵심 변경

기존 `test_compact_follow_up_intent_prompts_specify_density_bounds`에 3건 추가:
- `ai_contract`: `"2~5"` 포함 확인
- `memo_contract`: `"2~3"`, `"1~3"` 포함 확인
- `gen_contract`: `"2~4"` 포함 확인

---

## 검증

- `python3 -m py_compile tests/test_ollama_adapter.py` — 통과
- `python3 -m unittest -v tests.test_ollama_adapter` — **26 tests OK**

---

## 남은 리스크

- 없음. test-only slice.
