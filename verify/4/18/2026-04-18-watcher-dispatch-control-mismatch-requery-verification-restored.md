# 2026-04-18 watcher dispatch control mismatch requery verification restored

## 변경 파일
- 없음

## 사용 skill
- 없음

## 변경 이유
- `work/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery.md`가 same-day matching `/verify` 참조를 잃은 상태라 watcher startup이 이 round를 다시 `VERIFY_PENDING`으로 복원하고 있었습니다.
- current tree 기준으로 해당 `/work`의 핵심 주장이 여전히 유지되는지 다시 확인하고, explicit `work/...md` 참조가 들어간 matching verify artifact를 복원할 필요가 있었습니다.

## 핵심 변경
- 이 note는 `work/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery.md`를 직접 참조하는 restored verify artifact입니다.
- current tree에서 `watcher_dispatch.py::flush_pending()`의 active control 재조회와 structured mismatch reason/logging 경계가 여전히 남아 있음을 다시 확인했습니다.
- watcher 회귀는 현재 tree 기준 `tests.test_watcher_core` 전체로 다시 확인했고, same-day `/verify` 참조 복원 후에는 startup이 이 round를 "matching verify 없음"으로 다시 오인하지 않게 됩니다.

## 검증
- `python3 -m py_compile watcher_dispatch.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 123 tests`, `OK`

## 남은 리스크
- 이 restored verify note를 쓰기 전에 시작된 current run은 이미 `VERIFY_PENDING` job state를 들고 있을 수 있으므로, live runtime에는 한 번 더 restart/reload가 필요할 수 있습니다.
- same-day soak verification note는 여전히 다른 slug 파일에 남아 있으므로, 사람 눈에는 verify 파일명과 검증 대상이 완전히 예쁘게 정렬되지 않을 수 있습니다. automation matching은 explicit `work/...md` 참조 기준으로는 복구됐습니다.
