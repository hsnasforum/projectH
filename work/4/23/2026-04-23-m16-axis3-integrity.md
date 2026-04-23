# 2026-04-23 M16 Axis 3 integrity consolidation

## 변경 파일
- `model_adapter/ollama.py`
- `core/agent_loop.py`
- `tests/test_agent_loop_model_routing.py`
- `app/frontend/vite.config.ts`
- `app/static/dist/index.html`
- `app/static/dist/assets/index-Chj1x-63.css` 삭제
- `app/static/dist/assets/index-ZWNljoPw.js` 삭제
- `app/static/dist/assets/index.css` 생성됨, 현재 ignore 상태
- `app/static/dist/assets/index.js` 생성됨, 현재 ignore 상태
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m16-axis3-integrity.md`

## 사용 skill
- `doc-sync`: M16 Axis 3 shipped 기록을 `docs/MILESTONES.md`에 반영했습니다.
- `finalize-lite`: 지정 검증 결과와 sandbox로 실행되지 못한 항목을 구분했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 실패 사유, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- advisory seq 46 / implement handoff seq 47 기준 M16 Axis 3 integrity consolidation을 구현해야 했습니다.
- 이전 라우팅 활성화 후 `qwen2.5:14b`가 설치되지 않은 환경에서 heavy route가 즉시 실패할 수 있었습니다.
- Vite 기본 hash asset 이름은 tracked `app/static/dist` 산출물과 불일치가 반복되어 fixed-name asset 출력 정책이 필요했습니다.

## 핵심 변경
- `OllamaModelAdapter`에 `_cached_available_models`를 추가하고, `list_models()` 성공 결과를 `frozenset`으로 캐시하도록 했습니다.
- `is_model_available()`을 추가해 첫 호출에서 모델 목록을 채우고, Ollama 연결 확인이 실패하면 기존 동작을 깨지 않도록 available로 간주합니다.
- `AgentLoop._routed_model()`은 Ollama adapter일 때 HEAVY→MEDIUM→LIGHT, MEDIUM→LIGHT 순서로 설치된 tier 모델을 찾아 사용하고, 모두 없으면 `_NoOpContext`로 떨어집니다.
- `tests/test_agent_loop_model_routing.py`에 heavy tier fallback과 전체 tier unavailable no-op 경로를 검증하는 테스트 2개를 추가했습니다.
- `vite.config.ts`에 fixed-name `rollupOptions.output`을 추가했고, Vite build 결과 `index.html`은 `/assets/index.js`와 `/assets/index.css`를 참조합니다.
- `docs/MILESTONES.md`의 M16 shipped infrastructure를 Axis 1-3으로 갱신했습니다.

## 검증
- `python3 -m py_compile model_adapter/ollama.py core/agent_loop.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_agent_loop_model_routing tests.test_ollama_adapter -v`
  - 실패: `tests.test_agent_loop_model_routing` 5개는 통과했지만, `tests.test_ollama_adapter.OllamaAdapterTest.setUpClass`에서 fake HTTP server 바인딩이 sandbox에 막혀 `PermissionError: [Errno 1] Operation not permitted`가 발생했습니다.
- `python3 -m unittest tests.test_agent_loop_model_routing -v`
  - 통과: `Ran 5 tests`
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `cd app/frontend && npx vite build`
  - 통과: `index.css`, `index.js` fixed-name asset 생성 확인
  - 참고: Vite CJS Node API deprecation warning이 출력됐습니다.
- `find app/static/dist/assets -maxdepth 1 -type f -printf '%f\n' | sort`
  - 확인: `index.css`, `index.js`
- `git diff --check -- model_adapter/ollama.py core/agent_loop.py app/frontend/vite.config.ts docs/MILESTONES.md`
  - 통과: 출력 없음
- `git diff --check -- model_adapter/ollama.py core/agent_loop.py tests/test_agent_loop_model_routing.py app/frontend/vite.config.ts docs/MILESTONES.md app/static/dist/index.html`
  - 통과: 출력 없음

## 남은 리스크
- `_cached_available_models`는 Ollama server restart나 이후 `ollama pull` 결과를 자동 무효화하지 않습니다. handoff boundary대로 cache invalidation은 추가하지 않았습니다.
- Ollama 연결 자체가 실패하면 `is_model_available()`은 True를 반환해 기존 call path로 진행합니다. 즉 연결 장애는 fallback으로 숨기지 않고 기존 runtime error surface에 맡깁니다.
- `tests.test_ollama_adapter` 전체는 현재 sandbox의 로컬 socket bind 제한 때문에 이번 라운드에서 완료 통과를 확인하지 못했습니다.
- Vite build로 기존 tracked hash asset은 삭제되고 fixed-name `index.css`/`index.js`가 생성됐지만, 새 asset은 현재 `.gitignore` 때문에 ignored 상태입니다. handoff대로 `git rm --cached`나 `git add -f`는 실행하지 않았고 verify lane tracking follow-up이 필요합니다.
- 작업 전부터 `app/handlers/chat.py`, `tests/test_web_app.py`, `work/4/23/2026-04-23-ollama-routing-activation.md`에 수정이 있었으며 이번 round에서는 건드리지 않았습니다.
