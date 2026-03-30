# 2026-03-30 소설형 요약 reduce 개선

## 변경 파일
- `core/agent_loop.py`
- `model_adapter/ollama.py`
- `model_adapter/mock.py`
- `tests/test_ollama_adapter.py`
- `tests/test_smoke.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/3/30/2026-03-30-story-summary-reduce-improvement.md`

## 사용 skill
- `doc-sync`
  - 요약 동작 변경을 현재 구현 truth에 맞춰 제품 문서에 반영하기 위해 사용했습니다.
- `release-check`
  - 코드, 테스트, 브라우저 스모크, 문서 동기화 상태를 함께 확인하기 위해 사용했습니다.
- `work-log-closeout`
  - 오늘 라운드의 실제 변경과 검증 결과를 `/work`에 정직하게 남기기 위해 사용했습니다.

## 변경 이유
- 로컬 LLM 요약이 긴 서사 텍스트에서 줄거리 요약보다 인상적인 문장 발췌처럼 보이는 문제가 있었습니다.
- 기존 구현은 긴 문서를 chunk로 나눈 뒤, chunk별 요약을 다시 모델에게 통합시키지 않고 몇 줄만 선택해 붙이는 방식이라 소설형 텍스트의 전체 흐름을 잃기 쉬웠습니다.
- current MVP 범위를 넓히지 않으면서도, long-form summary 품질을 개선하는 가장 작은 범위는 summary prompt 보강과 chunk reduce 단계 재구성이었습니다.

## 핵심 변경
- `model_adapter/ollama.py`
  - summary system prompt를 강화해 narrative/fiction 텍스트에서는 인물, 핵심 사건, 갈등 변화, 마지막 상태를 우선 요약하도록 했습니다.
  - informational/argumentative 문서는 topic, main points, decisions/actions, conclusion을 우선하도록 함께 명시했습니다.
- `core/agent_loop.py`
  - 긴 문서 요약 시 chunk notes를 다시 하나의 reduce prompt로 묶어 최종 summary를 생성하도록 바꿨습니다.
  - 기존처럼 summary chunks는 그대로 유지하되, final response text는 isolated line pick보다 전체 흐름 재구성에 더 가깝게 만들었습니다.
- `model_adapter/mock.py`
  - 새 merged chunk outline prompt를 이해하는 mock summary path를 추가해 기존 smoke/web 회귀가 깨지지 않게 맞췄습니다.
- 테스트
  - `tests/test_ollama_adapter.py`에서 summary prompt가 narrative / informative guidance를 포함하는지 고정했습니다.
  - `tests/test_smoke.py`에 long narrative text가 merged chunk outline reduce를 통해 한 문장 흐름으로 요약되는 회귀를 추가했습니다.
- 문서
  - `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`에 long summary reduce와 narrative-priority summary behavior를 현재 shipped truth로 반영했습니다.

## 검증
- 실행:
  - `python3 -m py_compile core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py`
  - `python3 -m unittest -v tests.test_ollama_adapter tests.test_smoke tests.test_web_app`
  - `git diff --check`
  - `make e2e-test`
- 결과:
  - syntax check 통과
  - `tests.test_ollama_adapter`, `tests.test_smoke`, `tests.test_web_app` 통과
  - `git diff --check` 통과
  - Playwright smoke `12 passed (3.4m)`

## 남은 리스크
- 이번 라운드는 summary prompt와 chunk reduce를 개선한 것이지, 문서 유형을 명시적으로 분류하는 separate narrative mode를 추가한 것은 아닙니다.
- 실제 long-form summary 품질은 여전히 로컬 모델 크기와 추론 성능에 영향을 받습니다. 작은 모델에서는 개선돼도 완전한 plot compression이 항상 보장되지는 않습니다.
- `summary_chunks`는 여전히 evidence/anchor 성격의 보조 메타데이터이며, final summary와 별개로 heuristic selection을 사용합니다.
- 다음 slice가 필요하다면, 문서 유형 감지 없이도 적용 가능한 범위에서 summary reduce prompt를 search summary와 narrative summary에 더 다르게 주는지 검토할 수 있습니다.
