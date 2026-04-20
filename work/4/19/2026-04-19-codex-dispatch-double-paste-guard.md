# 2026-04-19 codex dispatch double paste guard

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `work/4/19/2026-04-19-codex-dispatch-double-paste-guard.md`

## 사용 skill
- `doc-sync`: Codex verify dispatch 계약 변경을 `.pipeline/README.md`와 코드 truth에 맞춰 좁게 동기화하기 위해 사용했습니다.
- `work-log-closeout`: 이번 watcher dispatch 중복 paste 방지 라운드의 `/work` closeout을 repo 규약 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- 실제 pane 스크린샷에서 같은 verify prompt가 Codex pane에 두 번 paste된 흔적이 확인됐습니다.
- 원인 후보를 코드 owner 기준으로 좁혀보면, `_dispatch_codex()`는 prompt가 실제로 소비된 뒤에도 immediate busy/activity 확인이 늦으면 `False`를 반환했고, 상위 verify FSM은 이를 dispatch 실패로 보고 동일 prompt를 재시도할 수 있었습니다.
- 즉 문제의 owner는 상위 watcher retry heuristic이 아니라 Codex dispatch helper의 성공/실패 경계였습니다. prompt consumed 상태를 실패로 되돌리면 delayed `DISPATCH_SEEN` / `TASK_ACCEPTED` 경로가 두 번째 paste를 유발할 수 있습니다.

## 핵심 변경
- `watcher_core.py::_dispatch_codex()`를 수정해, input cursor가 사라져 prompt가 실제로 소비된 뒤에는 immediate working indicator나 response activity가 아직 없어도 dispatch 자체는 성공(`True`)으로 간주하도록 바꿨습니다.
- 같은 상황에서는 `"codex dispatch consumed without immediate confirmation: defer acceptance to wrapper events"` 로그를 남기고, 이후 acceptance 판정은 wrapper `DISPATCH_SEEN` / `TASK_ACCEPTED` deadline 경로가 맡도록 고정했습니다.
- prompt가 끝까지 소비되지 않은 경우만 여전히 `False`를 반환하게 유지해, 진짜 미전송/미제출 경로와는 구분했습니다.
- `tests/test_watcher_core.py`의 Codex dispatch confirmation 테스트를 갱신해:
  - prompt consumed + no immediate confirmation -> `True`
  - prompt never consumed -> `False`
  를 각각 직접 고정했습니다.
- `.pipeline/README.md`에도 같은 계약을 적어, prompt consumed를 dispatch 실패로 되돌리지 않고 acceptance는 wrapper deadline이 맡는다는 경계를 문서화했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest`
  - 결과: `Ran 6 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 130 tests`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 출력 없음

## 남은 리스크
- 이번 라운드는 “prompt consumed 후 false 반환으로 인한 재paste” 경로를 줄인 것입니다. 실제 live tmux/Codex 세션에서 vendor UI가 prompt를 소비하지 않고 다른 형태로 바뀌는 host-specific 사례까지 모두 닫은 것은 아닙니다.
- `DISPATCH_SEEN` / `TASK_ACCEPTED` 자체가 장시간 누락되는 근본 원인이 별도로 있으면, 이제는 중복 paste 대신 accept-deadline / dispatch-stall 경로로 surface될 가능성이 높습니다. 그 경우 owner는 wrapper event surface 또는 lane readiness 쪽입니다.
- current tree에는 watcher/manual-cleanup, controller cozy, runtime docs 등 unrelated dirty worktree가 계속 남아 있으므로, 이 라운드 커밋/리뷰 시에는 `watcher_core.py`, `tests/test_watcher_core.py`, `.pipeline/README.md`만 분리해서 보는 편이 안전합니다.
