# 2026-04-02 unsupported-claim uncertainty honesty

**범위**: ≥14B 모델 일반 응답 시스템 프롬프트에 불확실 정보 유보 표현 지시 추가
**근거**: compact(≤7B) 프롬프트에는 "유보적 표현" 지시가 있으나 full(≥14B) 프롬프트에는 빠져 있어 단정적 응답 생성 가능

---

## 변경 파일

- `model_adapter/ollama.py` — `_FULL_SYSTEM_RESPOND`에 hedging instruction 추가
- `tests/test_ollama_adapter.py` — full/compact 프롬프트 hedging 포함 여부 regression 2건 추가

---

## 사용 skill

- 없음

---

## 변경 이유

compact 프롬프트(≤7B)는 "불확실한 내용은 '~로 알려져 있습니다' 등 유보적 표현을 쓰세요"라는 지시가 있으나, full 프롬프트(≥14B)에는 "소스 없으면 추측하지 말라"만 있고 **소스가 있지만 약한 경우**의 hedging 지시가 없었음. ≥14B 모델이 단일 출처 정보를 확정적으로 서술할 수 있는 gap.

---

## 핵심 변경

`_FULL_SYSTEM_RESPOND`에 추가된 문장:
> "When evidence exists but is not cross-verified or comes from a single source, use hedging expressions such as '~로 알려져 있습니다', '~한 것으로 보입니다', or '~일 가능성이 있습니다' instead of stating it as confirmed fact."

---

## 검증

- `python3 -m py_compile model_adapter/ollama.py tests/test_ollama_adapter.py` — 통과
- `python3 -m unittest -v tests.test_ollama_adapter` — **24 tests OK** (기존 22 + 새 regression 2)
- mock adapter에는 영향 없음. Ollama 런타임에서만 실제 효과.

---

## 남은 리스크

1. **mock에서 효과 미확인**: mock은 고정 로직이라 hedging 지시를 따르지 않음. Ollama 실사용에서 확인 필요.
2. **entity card 경로의 "단일 출처 정보" 필터링**: `_select_entity_fact_card_claims()`의 weak claim gating은 이번 slice 범위 밖. 별도 follow-up 가능.
