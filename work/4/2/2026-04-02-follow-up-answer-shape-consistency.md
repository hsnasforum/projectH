# 2026-04-02 follow-up Q&A answer-shape consistency

**범위**: follow-up intent (action_items, memo, general) 프롬프트에 밀도 범위 가이드 추가
**근거**: key_points는 "exactly 3"으로 명시적이나, 나머지 intent는 밀도 범위가 없어 답변 형태 불일관

---

## 변경 파일

- `model_adapter/ollama.py` — 4개 intent의 system prompt + output contract에 밀도 범위 추가 (full + compact 양쪽)
- `tests/test_ollama_adapter.py` — full/compact 밀도 범위 regression 2건 추가

---

## 사용 skill

- 없음

---

## 변경 이유

| Intent | 이전 | 추가된 가이드 |
|--------|------|---------------|
| key_points | "exactly 3 bullets" | 변경 없음 (이미 일관) |
| action_items | "1 to 5 items" | "2 to 5 items" (최소 밀도 추가) |
| memo | "제목/핵심/다음 행동" | "핵심 2~3개, 다음 행동 1~3개" |
| general | "short paragraph" | "2~4 sentences" |

---

## 핵심 변경

full prompt, compact prompt, output contract 모두 동일 밀도 범위로 정렬. mock adapter에는 영향 없으며 Ollama 런타임에서만 실제 효과.

---

## 검증

- `python3 -m unittest -v tests.test_ollama_adapter` — **26 tests OK** (기존 24 + 새 2)

---

## 남은 리스크

- 없음. prompt-only 변경이며 mock에서는 효과 미발현.
