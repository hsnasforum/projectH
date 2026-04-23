# 2026-04-23 Ollama routing activation

## 변경 파일
- `core/agent_loop.py`
- `tests/test_agent_loop_model_routing.py`
- `work/4/23/2026-04-23-ollama-routing-activation.md`

## 사용 skill
- `finalize-lite`: 모델 호출 경로 변경의 검증 범위와 미검증 범위를 구분했습니다.
- `work-log-closeout`: 이번 구현 round의 변경 파일, 실행 검증, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- 사용자 피드백은 `mock`과 `ollama`의 체감 성능/품질 차이가 예전과 거의 같다는 것이었습니다.
- 확인 결과 `model_adapter.router`에는 light/medium/heavy tier가 이미 정의되어 있었지만, `AgentLoop._respond_with_active_context()`에서 `_routed_model(...)` context를 열었다가 바로 닫은 뒤 실제 모델 호출을 실행하는 경로가 있었습니다.
- 일반 응답과 요약 경로도 active preference budget은 tier 기준으로 계산하면서, 실제 Ollama 모델 호출 자체는 routed context로 감싸지 않아 선택 모델 하나만 계속 쓰는 구조였습니다.

## 핵심 변경
- `core/agent_loop.py`의 short summary, chunk summary, reduce summary 호출을 `with self._routed_model(task="summarize", ...)` 안에서 실행하도록 변경했습니다.
- active context 답변 경로는 `_routed_model(...)` context가 `stream_answer_with_context()` 생성과 `_collect_model_stream()` 실행 전체를 감싸도록 수정했습니다.
- 일반 응답 경로도 `with self._routed_model(task="respond")` 안에서 `stream_respond()`를 실행하도록 변경했습니다.
- 신규 `tests/test_agent_loop_model_routing.py`는 기본 Ollama model이 `qwen2.5:3b`일 때도 summarize/respond는 routed medium `qwen2.5:7b`, entity-card context는 routed heavy `qwen2.5:14b`로 실제 stream 호출 중 전환되는지 검증합니다.

## 검증
- `python3 -m py_compile core/agent_loop.py tests/test_agent_loop_model_routing.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_agent_loop_model_routing -v`
  - 통과: `3 tests`
- `python3 -m unittest tests.test_ollama_adapter -v`
  - 통과: `29 tests`
- `git diff --check -- core/agent_loop.py tests/test_agent_loop_model_routing.py`
  - 통과: 출력 없음

## 남은 리스크
- `mock`은 여전히 deterministic baseline이라 품질/성능 개선 대상이 아닙니다. 이번 변경은 `ollama` provider에서만 의미가 있습니다.
- 실제 체감 개선은 로컬에 `qwen2.5:7b` / `qwen2.5:14b`가 설치되어 있고 충분히 빠르게 로딩되는지에 달려 있습니다.
- heavy route가 이제 실제로 `qwen2.5:14b`를 호출할 수 있으므로, 14B 모델이 설치되어 있지 않은 환경에서는 entity-card/latest-update 같은 heavy 경로가 실패할 수 있습니다. 다음 slice로 tier 모델 availability 확인 또는 fallback policy를 추가하는 편이 안전합니다.
- 실제 Ollama 서버를 띄운 end-to-end 성능 비교는 실행하지 않았습니다. 이번 검증은 라우팅 context가 실제 stream 호출 중 적용되는지에 집중했습니다.
