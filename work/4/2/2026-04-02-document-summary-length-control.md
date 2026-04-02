# 2026-04-02 document summary length control

**범위**: local document summary 프롬프트에 타겟 길이 가이드라인 추가
**근거**: document-first MVP core loop에서 요약이 너무 짧거나 장황해질 수 있는 문제

---

## 변경 파일

- `core/agent_loop.py` — 3개 summary 프롬프트에 `Target length:` 지시 추가

---

## 사용 skill

- 없음

---

## 변경 이유

3개 summary 프롬프트(`chunk_note`, `short_summary`, `merged_chunk_outline`)에 "concise"라는 모호한 지시만 있고 구체적 길이 범위가 없었음. 모델이 1줄로 끝내거나 불필요하게 장황해질 수 있는 원인.

---

## 핵심 변경

| 프롬프트 | 타겟 길이 | 상한 |
|----------|-----------|------|
| `chunk_note` (구간별 노트) | 1~2문장 (50~150자) | 3문장 |
| `short_summary` (짧은 문서 직접 요약) | 3~5문장 (200~400자) | 8문장 |
| `merged_chunk_outline` (구간 통합 요약) | 5~8문장 (400~700자) | 10문장 |

각 프롬프트의 기존 지시("Return only concise Korean plain text...") 바로 앞에 `Target length:` 줄 추가. 모델의 기존 행동을 깨지 않으면서 길이 범위만 명시.

---

## 검증

- `python3 -m py_compile core/agent_loop.py` — 통과
- `python3 -m unittest -v tests.test_web_app` — **187 tests OK**
- `python3 -m unittest discover -s tests -p 'test_smoke*'` — **96 tests OK**
- mock adapter는 프롬프트 텍스트를 파싱하지 않으므로 기존 테스트에 영향 없음. Ollama 실행 시에만 실제 길이 조절 효과 발현.

---

## 남은 리스크

1. **mock adapter에서는 효과 미확인**: mock은 고정 로직으로 응답하므로 길이 지시를 따르지 않음. 실제 효과는 Ollama 런타임에서 확인 필요.
2. **search_results 분기에는 미적용**: 이번 slice는 local document summary만. 검색 결과 요약 분기의 길이 가이드라인은 별도 slice.
