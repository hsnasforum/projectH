STATUS: verified
CONTROL_SEQ: 142
BASED_ON_WORK: work/4/25/2026-04-25-m30-legacy-patch-proxy-cleanup.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 142 (M30 next slice direction)

---

## M30 Axis 2: legacy patch proxy cleanup

### Verdict

PASS. `_LegacyPatchableSharedCall` 프록시 및 `_install_legacy_patch_target` 7회 호출이 완전 제거되었고, `tests/test_watcher_core.py`의 patch target이 canonical `_shared_*` 이름으로 마이그레이션됨. 202 tests 전체 통과.

### Checks Run

- `grep -n "_LegacyPatchableSharedCall\|_install_legacy_patch_target" watcher_core.py` → 매치 없음 (exit 1)
- `python3 -m py_compile watcher_core.py` → OK (출력 없음)
- `python3 -m unittest tests/test_watcher_core.py -v 2>&1 | tail -5` → `Ran 202 tests in 8.684s` `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py` → exit 0 (공백 오류 없음)
- `rg -n 'watcher_core\.(_capture_pane_text|wait_for_pane_settle|...)' tests/test_watcher_core.py` → 매치 없음 (work 기술과 일치)

### What Was Not Checked

- `make e2e-test` 미재실행: 브라우저 계약 변경 없음, 변경 파일이 `watcher_core.py`와 `tests/test_watcher_core.py`에 한정.
- 다른 test suite 미재실행: 변경 범위가 watcher helper patch target에 국한되며, 다른 테스트 파일은 `WatcherTurnState` import 외 패치 의존 없음.

### Implementation Review

work 노트 기술과 일치:
- `_LegacyPatchableSharedCall` 클래스 삭제됨
- `_install_legacy_patch_target` 함수 삭제됨
- 7개 `_install_legacy_patch_target(...)` 호출 삭제됨
- `tests/test_watcher_core.py` legacy mock patch target 112곳 → canonical `_shared_*` 문자열로 교체됨
- `WatcherDispatchQueue`와 `StateMachine`에 넘기는 helper는 lambda로 감싸 생성-후 mock.patch 계약 유지

### M30 State After Axes 1–2

| Axis | 내용 | 상태 |
|---|---|---|
| Axis 1 (SEQ 136-137) | pane-surface stub 7개 제거, `_shared_*` 교체 | ✓ 완료 |
| Axis 2 (SEQ 141-142) | legacy patch proxy 제거, test target 마이그레이션 | ✓ 완료 |

### Next: Direction Advisory

M30 Axes 1–2로 watcher_core의 legacy proxy 과도기 부채가 제거됨. 추가 Axis (watcher_core.py 책임 단위 분리) 또는 다음 milestone 전환 여부는 advisory 판단이 필요함.
