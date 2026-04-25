# 2026-04-25 M33 watcher stabilizer 추출

## 변경 파일
- `watcher_core.py`
- `watcher_stabilizer.py`
- `work/4/25/2026-04-25-m33-watcher-stabilizer-extraction.md`

## 사용 skill
- `work-log-closeout`: 구현 파일, 검증 결과, 남은 리스크를 `/work` closeout으로 기록하기 위해 사용했습니다.

## 변경 이유
- M33 Axis 2 handoff에 따라 `watcher_core.py`에 남아 있던 아티팩트 해싱/안정화 책임을 `watcher_stabilizer.py`로 분리해 watcher core의 구조적 책임을 줄였습니다.

## 핵심 변경
- 신규 `watcher_stabilizer.py`를 추가하고 `compute_file_sha256`, `StabilizeSnapshot`, `ArtifactStabilizer`를 이동했습니다.
- `watcher_core.py`는 이동한 심볼을 `watcher_stabilizer`에서 import해 `watcher_core.compute_file_sha256(...)` 등 기존 re-export 접근을 유지합니다.
- `watcher_core.py`의 `dataclass` import는 더 이상 필요하지 않아 제거했습니다.
- `watcher_state.py`, `watcher_dispatch.py`, `watcher_signals.py`, 테스트 파일은 수정하지 않았습니다.
- 동작 경계: 기존 파일 해싱과 안정화 판정 로직만 모듈 이동했으며 새 파일 쓰기 위치, 권한 상승, 외부 네트워크, destructive 동작은 추가하지 않았습니다.

## 검증
- `python3 -m py_compile watcher_core.py watcher_stabilizer.py`
  - 통과, 출력 없음.
- `python3 -m unittest tests/test_watcher_core.py tests/test_watcher_signals.py tests/test_controller_monitor.py -v 2>&1 | tail -5`
  - `Ran 216 tests in 8.968s` / `OK`.
- `grep -n "^def compute_file_sha256\|^class StabilizeSnapshot\|^class ArtifactStabilizer" watcher_core.py`
  - 출력 없음. 대상 def/class 잔존 매치 없음.
- `git diff --check -- watcher_core.py watcher_stabilizer.py`
  - 통과, 출력 없음.

## 남은 리스크
- 이번 변경은 구조 이동이며 unit 테스트 묶음으로 기존 `watcher_core.*` re-export 계약을 확인했습니다. 실제 장시간 watcher runtime에서 artifact 안정화가 반복 수행되는 live 동작은 운영 중 자연 사용이나 별도 live smoke에서만 확인됩니다.
- docs 변경은 하지 않았습니다. 현재 shipped product contract나 사용자-facing 동작을 바꾸지 않는 내부 모듈 분리로 판단했습니다.
