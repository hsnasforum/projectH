# 2026-04-02 aggregate reversed-state surfacing hardening

**범위**: full single-worker `make e2e-test`에서 `aggregate-trigger-reversed` 표시가 간헐 실패하는 문제 수정
**근거**: `verify/4/2/2026-04-02-response-box-transcript-duplication-cleanup-verification.md` line 750 간헐 실패

---

## 변경 파일

- `app/static/app.js` — `renderSession` stale-render guard 추가 (session `updated_at` 비교)

---

## 사용 skill

- 없음

---

## 변경 이유

4번째 요청의 스트리밍이 아직 진행 중일 때 reverse 버튼을 클릭하면, reverse handler가 `renderSession(reversed_session_data)`로 reversed state를 렌더링한 뒤, 4번째 요청의 `renderResult`가 stale session snapshot(reverse 이전)으로 `renderSession`을 다시 호출하여 reversed state를 덮어씀. 결과적으로 `aggregate-trigger-reversed` badge가 사라짐.

---

## 핵심 변경

`renderSession(session)`에 stale-render guard 추가:
- 같은 session ID에 대해, 들어오는 `session.updated_at`이 마지막으로 렌더링된 `updated_at`보다 과거이면 렌더링을 skip
- 다른 session ID면 항상 렌더링
- `state._lastRenderedSessionUpdatedAt` 필드 추가

이로써 reverse handler의 최신 session data가 이미 렌더링된 후, stale한 `renderResult`의 session은 무시됨.

---

## 검증

- `python3 -m unittest -v tests.test_web_app` — **187 tests OK**
- targeted aggregate 테스트 10회 연속 — **10/10 passed**
- `make e2e-test` 3회 연속 — **16/16 × 3회 passed**

---

## 남은 리스크

1. **병렬 stress hardening**: 이번 fix는 single-worker 기준. 병렬 worker에서는 여전히 flaky할 수 있음. 이번 slice 범위 밖.
2. **React frontend 미연결**: 이번 slice 범위 밖.
