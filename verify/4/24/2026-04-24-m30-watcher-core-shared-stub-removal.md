STATUS: verified
CONTROL_SEQ: 137
BASED_ON_WORK: work/4/24/2026-04-24-m30-watcher-core-shared-stub-removal.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 137 (M30 Axis 2 — legacy patch proxy cleanup + test migration)

---

## M30 Axis 1: watcher_core pane-surface stub removal

### Verdict

PASS. stub 7개 제거 및 `_shared_*` 교체가 work 기술과 일치하고, 202 tests 통과 확인.

### Checks Run

- `python3 -m py_compile watcher_core.py` → OK (출력 없음)
- `python3 -m unittest tests/test_watcher_core.py -v 2>&1 | tail -8` → `Ran 202 tests in 9.487s` `OK`
- `grep -n "^def _capture_pane_text|^def wait_for_pane_settle|..." watcher_core.py` → 매치 없음 (stub def 모두 제거됨)
- Non-shared call sites 잔존 여부 확인 → 매치 없음 (모든 내부 호출이 `_shared_*`로 교체됨)

### What Was Not Checked

- `make e2e-test` 미재실행: 브라우저 계약 변경 없음, 소스는 `watcher_core.py`만 수정됨 (SCOPE_HINT: standard verification).
- `tests/test_watcher_core.py` 이외 테스트 미재실행: 다른 테스트 파일은 `watcher_core.WatcherTurnState` 열거형 import 외에 패치 의존 없음.

### Implementation Review

work 노트 기술과 일치함:
- stub def 7개 (`_capture_pane_text`, `wait_for_pane_settle`, `_pane_text_has_busy_indicator`, `_pane_text_has_input_cursor`, `_pane_text_is_idle`, `_pane_text_has_codex_activity`, `_pane_text_has_gemini_activity`) 삭제됨
- 보존 함수 4개 (`_line_looks_like_input_prompt`, `_pane_text_has_gemini_ready_prompt`, `_pane_has_input_cursor`, `_pane_has_working_indicator`) 유지됨
- 파일 크기: 5050 → 5031 lines (순 감소 확인; proxy 추가로 stub 완전 제거 대비 효과 감소됨)

### Identified Risk: Legacy Patch Proxy

Codex는 테스트 파일 수정 금지 제약 하에서 `_LegacyPatchableSharedCall` 프록시 메커니즘을 추가했다. 이 프록시는:
- `globals()[shared_name]` 및 `globals()[legacy_name]` 양쪽을 같은 프록시 객체로 설정
- 런타임 호출 시 shared fallback으로 정상 위임
- 테스트가 legacy 이름을 `unittest.mock.patch`로 교체할 때 해당 mock을 인터셉트

현재 `tests/test_watcher_core.py`에 legacy 이름을 패치하는 호출이 **120곳** 존재한다. 프록시는 행동 정확성을 유지하나 새 복잡도를 도입한다. 추후 `pipeline_runtime.lane_surface.*`를 직접 패치하도록 테스트를 갱신하면 제거 가능하다.

### M30 Axis 1 State

| 항목 | 상태 |
|---|---|
| stub def 7개 제거 | ✓ |
| 내부 call site `_shared_*` 교체 | ✓ |
| 보존 함수 4개 유지 | ✓ |
| 202 unit tests PASS | ✓ |
| legacy patch proxy (과도기) | ⚠ 정상 동작, 추후 정리 대상 |
