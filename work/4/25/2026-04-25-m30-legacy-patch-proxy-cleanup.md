# 2026-04-25 M30 legacy patch proxy cleanup

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `work/4/25/2026-04-25-m30-legacy-patch-proxy-cleanup.md`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- `CONTROL_SEQ: 141` implement handoff에 따라 M30 Axis 1에서 임시로 남긴 `_LegacyPatchableSharedCall` 프록시와 `_install_legacy_patch_target` 호출을 제거해야 했습니다.
- 테스트가 legacy `watcher_core._*` patch target을 계속 바라보면 프록시 제거 후 `tests/test_watcher_core.py`가 대량 실패하므로, patch target을 canonical `_shared_*` 이름으로 마이그레이션했습니다.

## 핵심 변경
- `watcher_core.py`에서 `_LegacyPatchableSharedCall`, `_install_legacy_patch_target`, 7개 legacy patch target 설치 호출을 삭제했습니다.
- legacy pane helper wrapper 제거 이후 남은 내부 호출은 canonical `_shared_*` helper를 직접 사용하도록 유지했습니다.
- `tests/test_watcher_core.py`의 legacy mock patch target 문자열을 canonical `watcher_core._shared_*` 문자열로 교체했습니다.
- 프록시 제거 후 직접 helper assertion 9곳도 동일 기대값을 유지한 채 canonical `_shared_*` 호출로 맞췄습니다.
- `WatcherDispatchQueue`와 `StateMachine`에 넘기는 pane helper는 lambda로 감싸, 생성 이후 `mock.patch("watcher_core._shared_*")`가 호출 시점에 반영되는 기존 테스트 계약을 유지했습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `978b18b6a854798b4d9f35e040b21168cf75a7086f014d7bb1c76c3e4fe9db17`
- `python3 -m py_compile watcher_core.py`
  - 통과: 출력 없음
- `grep -n "_LegacyPatchableSharedCall\|_install_legacy_patch_target" watcher_core.py`
  - 통과: 매치 없음, exit code 1
- `git diff --check -- watcher_core.py tests/test_watcher_core.py`
  - 통과: 출력 없음
- `rg -n 'watcher_core\.(_capture_pane_text|wait_for_pane_settle|_pane_text_has_busy_indicator|_pane_text_has_input_cursor|_pane_text_is_idle|_pane_text_has_codex_activity|_pane_text_has_gemini_activity)' tests/test_watcher_core.py`
  - 통과: 매치 없음, exit code 1
- `python3 -m unittest tests/test_watcher_core.py -v 2>&1 | tail -5`
  - 초기 실행: `Ran 202 tests`, `FAILED (failures=22, errors=3)`
  - 원인: shared helper를 생성자에서 직접 함수 객체로 주입해, 테스트의 canonical `mock.patch("watcher_core._shared_*")`가 생성 후 주입된 함수에 닿지 않았습니다.
  - 수정 후 재실행 통과: `Ran 202 tests`, `OK`

## 남은 리스크
- 이번 slice는 `watcher_core.py`와 `tests/test_watcher_core.py`의 legacy patch proxy 제거와 테스트 target 마이그레이션만 다뤘습니다.
- 작업 시작 전 repo에는 다른 파일의 dirty state가 이미 많았고, 이 closeout은 이번 handoff에서 직접 변경한 파일만 기록합니다.
- browser/E2E나 전체 unittest는 실행하지 않았습니다. 변경 범위가 watcher core helper patch target과 해당 단위 테스트에 한정되어 `tests/test_watcher_core.py` 전체를 좁은 검증으로 삼았습니다.
