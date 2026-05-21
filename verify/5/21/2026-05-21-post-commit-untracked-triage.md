# verify: 2026-05-21 post-commit untracked file triage

## 검증 결과

커밋 6개 완료. tracked 변경 없음 확인.
untracked 소스 파일 중 **테스트 1개 실패** 발견.

## 커밋 완료 확인

| 커밋 | 내용 |
|---|---|
| 2ff9046 | fix(launcher): P1-P18 pipeline launcher bugfix bundle + runs auto-cleanup |
| b84570d | docs: sync docs and README |
| 720c7f6 | feat(watcher): harden dispatch and verify recovery |
| 7f3f337 | feat(app): sync controller and launcher surfaces |
| fc4263c | test: update runtime and web smoke coverage |
| f4dc447 | test(e2e): update controller and web smoke scenarios |

Playwright: web-smoke 165개, controller-smoke 20개 PASS 확인.

## untracked 파일 분류

| 파일 | 종류 | 판정 |
|---|---|---|
| `.pipeline/.supervisor-start.lock` | 런타임 잠금 파일 | **gitignore 추가 필요** |
| `controller/js/queue-presentation.js` | 신규 JS 모듈 | 테스트 실패로 블로킹 |
| `pipeline_runtime/state_contract.py` | 신규 Python 모듈 | 컴파일 OK, 테스트 PASS |
| `tests/local_socket_guard.py` | 신규 Python 헬퍼 | 컴파일 OK, 테스트 PASS |
| `tests/test_local_socket_guard.py` | 신규 테스트 | PASS |
| `tests/test_pipeline_runtime_state_contract.py` | 신규 테스트 | PASS |
| `tests/test_controller_queue_presentation.py` | 신규 테스트 | **FAIL** |
| `tests/fixtures/` | 테스트 픽스처 | 테스트 통과 조건부 |
| `docs/superpowers/plans/2026-05-21-pipeline-launcher-bugfixes.md` | 계획서 | 커밋 가능 |
| `report/gemini/2026-05-21-launcher-analysis.md` | 분석 리포트 | 커밋 가능 |
| `work/`, `verify/` 기록들 | 프로젝트 히스토리 | 커밋 가능 |

## 실패 상세

**`test_controller_queue_presentation`** — 18개 중 1개 실패

```
SyntaxError: Named export 'PipelineState' not found.
controller/js/state.js is a CommonJS module.
```

`controller/js/queue-presentation.js`가 `state.js`를 ESM named export로 import하려 했으나
`state.js`는 CommonJS 형식이라 Node ESM에서 named import 불가.

수정 방향: `queue-presentation.js` import를 CommonJS-compatible 방식으로 변경:
```js
// Before
import { PipelineState } from './controller/js/state.js';

// After
import pkg from './controller/js/state.js';
const { PipelineState } = pkg;
```

## 다음 action 2건

1. **즉시 가능**: `.pipeline/.supervisor-start.lock`을 `.gitignore`에 추가
2. **Codex 구현**: `queue-presentation.js` ESM/CommonJS import 수정 → 테스트 통과 후 untracked 소스 파일 전체 커밋
