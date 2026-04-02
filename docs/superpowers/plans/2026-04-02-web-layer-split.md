# web.py 계층별 분리 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** app/web.py 7,025줄을 5개 파일로 분리하여 파일당 800~2,500줄로 줄이기

**Architecture:** WebAppService를 mixin 기반으로 분리. 각 mixin은 독립 파일에 위치하며 self를 통해 공유 상태(session_store, task_logger 등)에 접근. 라우트 등록은 LocalAssistantHandler에 유지.

**Tech Stack:** Python 3.11, stdlib http.server, 기존 테스트 unittest

---

### Task 1: SerializerMixin 추출

**Files:**
- Create: `app/serializers.py`
- Modify: `app/web.py`
- Test: 기존 `tests/test_web_app.py` (변경 없이 통과해야 함)

- [ ] **Step 1: app/serializers.py 생성 — 모든 _serialize_* 메서드 이동**

web.py에서 `_serialize_` 로 시작하는 25개 메서드를 `SerializerMixin` 클래스로 추출.

```python
# app/serializers.py
from __future__ import annotations
from typing import Any
from app.localization import localize_text


class SerializerMixin:
    """직렬화 메서드 모음. WebAppService에서 mixin으로 사용."""

    def _serialize_response(self, response: Any) -> dict[str, Any]:
        # web.py의 _serialize_response 메서드 본문 그대로 이동
        ...

    def _serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        ...

    # ... 나머지 23개 _serialize_* 메서드 전부 이동
```

web.py에서 해당 메서드들 삭제하고 import:

```python
# app/web.py 상단
from app.serializers import SerializerMixin

class WebAppService(SerializerMixin):
    ...
```

- [ ] **Step 2: 테스트 실행**

Run: `python -m unittest tests.test_web_app -v 2>&1 | tail -5`
Expected: 186 tests OK

- [ ] **Step 3: 커밋**

```bash
git add app/serializers.py app/web.py
git commit -m "refactor: extract SerializerMixin from web.py (25 methods)"
```

---

### Task 2: PreferenceHandlerMixin 추출

**Files:**
- Create: `app/handlers/__init__.py`
- Create: `app/handlers/preferences.py`
- Modify: `app/web.py`

- [ ] **Step 1: handlers 디렉터리 + preferences.py 생성**

```python
# app/handlers/__init__.py
(빈 파일)
```

```python
# app/handlers/preferences.py
from __future__ import annotations
from typing import Any


class PreferenceHandlerMixin:
    """선호 관리 핸들러. WebAppService에서 mixin으로 사용."""

    def list_preferences_payload(self) -> dict[str, Any]:
        # web.py 445~452 이동
        ...

    def activate_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 454~462 이동
        ...

    def pause_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 464~472 이동
        ...

    def reject_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 474~482 이동
        ...
```

web.py에서 4개 메서드 삭제, mixin 추가:

```python
from app.handlers.preferences import PreferenceHandlerMixin

class WebAppService(SerializerMixin, PreferenceHandlerMixin):
    ...
```

- [ ] **Step 2: 테스트 실행**

Run: `python -m unittest tests.test_web_app -v 2>&1 | tail -5`
Expected: 186 tests OK

- [ ] **Step 3: 커밋**

```bash
git add app/handlers/ app/web.py
git commit -m "refactor: extract PreferenceHandlerMixin from web.py"
```

---

### Task 3: FeedbackHandlerMixin 추출

**Files:**
- Create: `app/handlers/feedback.py`
- Modify: `app/web.py`

- [ ] **Step 1: feedback.py 생성 — 4개 메서드 이동**

```python
# app/handlers/feedback.py
from __future__ import annotations
from typing import Any


class FeedbackHandlerMixin:
    """피드백/교정/판정 핸들러."""

    def submit_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 155~191 이동
        ...

    def submit_correction(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 193~295 이동
        ...

    def submit_content_verdict(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 297~366 이동
        ...

    def submit_content_reason_note(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 368~427 이동
        ...
```

web.py에서 mixin 추가:

```python
from app.handlers.feedback import FeedbackHandlerMixin

class WebAppService(SerializerMixin, PreferenceHandlerMixin, FeedbackHandlerMixin):
```

- [ ] **Step 2: 테스트 실행**

Expected: 186 tests OK

- [ ] **Step 3: 커밋**

```bash
git add app/handlers/feedback.py app/web.py
git commit -m "refactor: extract FeedbackHandlerMixin from web.py"
```

---

### Task 4: AggregateHandlerMixin 추출

**Files:**
- Create: `app/handlers/aggregate.py`
- Modify: `app/web.py`

- [ ] **Step 1: aggregate.py 생성 — 8개 메서드 이동**

```python
# app/handlers/aggregate.py
from __future__ import annotations
from typing import Any


class AggregateHandlerMixin:
    """후보 확인/리뷰/집계 트랜지션 핸들러."""

    def submit_candidate_confirmation(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 484~569 이동
        ...

    def submit_candidate_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 571~682 이동
        ...

    def emit_aggregate_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 684~760 이동
        ...

    def apply_aggregate_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 762~818 이동
        ...

    def confirm_aggregate_transition_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 820~901 이동
        ...

    def stop_apply_aggregate_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 903~963 이동
        ...

    def reverse_aggregate_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 965~1017 이동
        ...

    def check_aggregate_conflict_visibility(self, payload: dict[str, Any]) -> dict[str, Any]:
        # web.py 1019~1143 이동
        ...
```

- [ ] **Step 2: 테스트 실행**

Expected: 186 tests OK

- [ ] **Step 3: 커밋**

```bash
git add app/handlers/aggregate.py app/web.py
git commit -m "refactor: extract AggregateHandlerMixin from web.py"
```

---

### Task 5: ChatHandlerMixin 추출

**Files:**
- Create: `app/handlers/chat.py`
- Modify: `app/web.py`

- [ ] **Step 1: chat.py 생성 — 채팅 코어 메서드 이동**

이동 대상:
- `handle_chat` (1145)
- `cancel_stream` (1148)
- `stream_chat` (1180) + 내부 `push_stream_event`, `worker`
- `_handle_chat_impl` (1260~1541)
- `_apply_reviewed_memory_effects` (1541~1578)
- `_build_model_router` (1580)
- `_build_tools` (1590)
- `_maybe_preflight_model` (1600)
- `_emit_phase` (1617)
- `_stream_request_key` (1638)
- `_build_user_text` (1641)
- `_build_metadata` (1668)
- `_parse_uploaded_file` (1715)
- `_parse_uploaded_search_files` (1726)
- `_parse_uploaded_file_record` (1746)

```python
# app/handlers/chat.py
from __future__ import annotations
import threading
from typing import Any, Callable
# ... 필요한 import

class ChatHandlerMixin:
    """채팅 스트리밍/처리 핸들러."""

    def handle_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def cancel_stream(self, *, session_id: str | None, request_id: str | None) -> dict[str, Any]:
        ...

    def stream_chat(self, payload: dict[str, Any]):
        ...

    def _handle_chat_impl(self, ...):
        ...

    # ... 나머지 private 메서드들
```

- [ ] **Step 2: 테스트 실행**

Run: `python -m unittest tests.test_web_app tests.test_smoke tests.test_http_integration -v 2>&1 | tail -5`
Expected: 304 tests OK

- [ ] **Step 3: 커밋**

```bash
git add app/handlers/chat.py app/web.py
git commit -m "refactor: extract ChatHandlerMixin from web.py"
```

---

### Task 6: web.py 정리 + 최종 검증

**Files:**
- Modify: `app/web.py`

- [ ] **Step 1: web.py 확인 — 800줄 이하인지 검증**

```bash
wc -l app/web.py
# Expected: ~800줄 이하
```

남은 내용:
- WebAppService.__init__
- render_index, get_config, list_sessions_payload, get_session_payload
- delete_session, delete_all_sessions
- _normalize_optional_text 등 공통 유틸
- _build_response_origin 등 라우트에서 직접 쓰는 메서드
- LocalAssistantHandler (라우트 등록)
- LocalOnlyHTTPServer
- run_web_server

- [ ] **Step 2: 전체 테스트 실행**

```bash
python -c "
import unittest, sys
for m in ['tests.test_web_app','tests.test_smoke','tests.test_http_integration','tests.test_eval_harness','tests.test_ollama_adapter','tests.test_preference_injection']:
    __import__(m); suite=unittest.TestLoader().loadTestsFromModule(sys.modules[m])
    r=unittest.TextTestRunner(verbosity=0).run(suite)
    print(f'{m}: {r.testsRun} - {\"OK\" if r.wasSuccessful() else \"FAIL\"}')
"
```
Expected: 모두 OK

- [ ] **Step 3: 서버 기동 확인**

```bash
timeout 5 python -m app.web &
sleep 2
curl -s http://127.0.0.1:8765/healthz
# Expected: {"ok": true}
kill %1
```

- [ ] **Step 4: 최종 커밋**

```bash
git add -A
git commit -m "refactor: web.py split complete — 7,025 → ~800 lines"
git push origin master
```

---

## 검증 요약

| 단계 | 파일 | 추출 메서드 수 | 예상 줄 수 |
|------|------|---------------|-----------|
| Task 1 | serializers.py | 25 | ~900 |
| Task 2 | handlers/preferences.py | 4 | ~200 |
| Task 3 | handlers/feedback.py | 4 | ~600 |
| Task 4 | handlers/aggregate.py | 8 | ~1,500 |
| Task 5 | handlers/chat.py | 15+ | ~2,500 |
| Task 6 | web.py (잔여) | — | ~800 |
