# 2026-03-31 fiction / narrative summary faithfulness hardening

## 변경 파일
- `core/agent_loop.py`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- 소설/서사문 요약 시 원문에 없는 사건 추가, 구체적 단어 치환(예: '전시'→'공연'), 인물 관계 결론을 원문보다 앞질러 단정하는 요약 왜곡 발생
- 기존 prompt는 "major characters, key events, conflict changes, ending state"를 요약하라고만 지시하고, 원문에 없는 내용을 추가하지 말라는 명시적 금지 규칙이 없었음

## 핵심 변경

### prompt 변경 (3곳, local_document path만)
`_build_individual_chunk_summary_prompt`, `_build_short_summary_prompt`, `_build_chunk_summary_reduce_prompt`의 local document branch에 동일한 STRICT 규칙 추가:

```
STRICT: Only include events, facts, and conclusions that appear explicitly in the [excerpt/text/chunk notes].
Do not add events that did not happen,
substitute different words for specific terms (e.g. replacing '전시' with '공연'),
or state relationship outcomes or plot conclusions beyond what the [text/notes] actually [shows/contain].
```

### 변경하지 않은 것
- search_results path: 변경 없음 (이미 "source-backed" 규칙이 별도로 존재)
- summary source-type split 구조: 유지
- mock adapter: 변경 없음 (mock은 prompt를 해석하지 않음)
- browser-visible UI: 변경 없음

### docs 반영
- `docs/ACCEPTANCE_CRITERIA.md`: narrative summary에 source-anchored faithfulness 규칙 명시

## 검증
- `python3 -m py_compile core/agent_loop.py` — 통과
- `python3 -m unittest -v tests.test_web_app` — `98 tests OK`
- `python3 -m unittest -v tests.test_smoke` — `86 tests OK`
- `git diff --check` (변경 파일) — 통과
- `make e2e-test` — browser-visible contract를 바꾸지 않았으므로 생략. summary prompt 변경은 모델 응답 내용에만 영향하며, mock adapter는 prompt를 해석하지 않으므로 E2E에서 차이가 없음.

## 남은 리스크
- prompt 규칙 추가만으로는 모든 hallucination을 방지할 수 없음. 실제 효과는 Ollama 등 실제 모델에서 narrative 문서를 요약해 봐야 확인 가능
- mock adapter는 prompt를 해석하지 않으므로 이 규칙의 효과를 자동 테스트로 검증할 수 없음. 실제 모델 기반 eval fixture가 필요 (later scope)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
