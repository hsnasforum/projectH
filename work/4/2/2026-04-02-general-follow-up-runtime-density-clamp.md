# 2026-04-02 general follow-up runtime density clamp

**범위**: `general` follow-up 경로에 최소 runtime postprocess 추가 — 메타데이터 필터 + 2~4문장 clamp
**근거**: `verify/4/2/2026-04-02-compact-density-output-contract-regression-verification.md` — `general` follow-up 경로는 `2~4문장` contract를 prompt/output-contract 문자열로만 선언하고 runtime postprocess가 없어 출력 shape drift 가능성이 남아 있었음

---

## 변경 파일

- `model_adapter/ollama.py` — `_postprocess_answer`의 `general` fallback을 `_postprocess_general` 호출로 교체, `_postprocess_general` 메서드 추가
- `tests/test_ollama_adapter.py` — `test_general_postprocess_filters_metadata_and_clamps_sentences`, `test_general_postprocess_preserves_short_answer` 2건 추가

---

## 사용 skill

- 없음

---

## 변경 이유

이전 라운드에서 compact output contract의 `2~4문장` 규칙을 prompt 문자열과 output contract 문자열에 선언했으나, `_postprocess_answer`의 `general` 분기는 `raw_answer.strip()`만 반환하고 있어 실제 runtime에서 밀도 규칙이 적용되지 않았음. `key_points`, `action_items`, `memo`는 이미 postprocess가 있으나 `general`만 빠져 있었음.

---

## 핵심 변경

1. `_postprocess_answer` (line 623): `return raw_answer.strip()` → `return self._postprocess_general(raw_answer=raw_answer)`
2. `_postprocess_general` 메서드 추가:
   - `_split_sentences`로 문장 분리
   - `_looks_like_metadata`로 메타데이터성 문장 필터
   - 필터 후 결과가 비면 원본 문장 유지 (fallback)
   - 최대 4문장으로 clamp
   - `" ".join()`으로 단일 문단 결합
3. 테스트 2건:
   - 메타데이터 필터 + 4문장 clamp 확인
   - 짧은 정상 응답 보존 확인

---

## 검증

- `python3 -m py_compile model_adapter/ollama.py tests/test_ollama_adapter.py` — 통과
- `python3 -m unittest -v tests.test_ollama_adapter` — **28 tests OK** (기존 26 + 신규 2)

---

## 남은 리스크

- `stream_answer_with_context`의 `general` 경로도 postprocess를 거치므로 streaming에서도 동일하게 clamp가 적용됨 (line 335-342의 `_postprocess_answer` → `text_replace` event). 별도 리스크 없음.
- full (>14B) 모델의 `general` 경로도 같은 `_postprocess_answer`를 타므로 동일하게 적용됨.
