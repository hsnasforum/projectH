# 2026-04-25 M33 watcher state 추출

## 변경 파일
- `watcher_core.py`
- `watcher_state.py`
- `work/4/25/2026-04-25-m33-watcher-state-extraction.md`

## 사용 skill
- `security-gate`: lease lock, dispatch/suppressed jsonl, manifest read/validate 경계가 파일 쓰기와 런타임 coordination 상태를 다루므로 이동 후 위험 경계를 확인했습니다.
- `work-log-closeout`: 구현 파일, 검증 결과, 남은 리스크를 `/work` closeout으로 기록하기 위해 사용했습니다.

## 변경 이유
- M33 Axis 1 handoff에 따라 `watcher_core.py`에 남아 있던 coordination state 모델과 state 관리 클래스를 `watcher_state.py`로 분리해 watcher core의 구조적 책임을 줄였습니다.

## 핵심 변경
- 신규 `watcher_state.py`를 추가하고 `WatcherTurnState`, `LeaseData`, `ControlSignal`, `PaneLease`, `DedupeGuard`, `ManifestCollector`를 이동했습니다.
- optional `jsonschema` import와 `_JSONSCHEMA_AVAILABLE` truth를 `watcher_state.py`로 이동했습니다.
- `watcher_core.py`는 이동한 심볼을 `watcher_state`에서 import해 `watcher_core.WatcherTurnState`, `watcher_core.PaneLease` 등 기존 re-export 접근을 유지합니다.
- `compute_file_sha256`, `StabilizeSnapshot`, `ArtifactStabilizer`는 handoff 범위대로 `watcher_core.py`에 남겼습니다.
- 보안 경계: 기존 lock 파일, dispatch/suppressed jsonl, manifest read/validation 경로만 모듈 이동했고 새 파일 쓰기 위치, 권한 상승, 외부 네트워크, destructive 동작은 추가하지 않았습니다.

## 검증
- `python3 -m py_compile watcher_core.py watcher_state.py`
  - 통과, 출력 없음.
- `python3 -m unittest tests/test_watcher_core.py tests/test_watcher_signals.py tests/test_controller_monitor.py -v 2>&1 | tail -5`
  - `Ran 216 tests in 8.419s` / `OK`.
- `grep -n "^class WatcherTurnState\|^class PaneLease\|^class DedupeGuard\|^class ManifestCollector\|^class LeaseData\|^class ControlSignal" watcher_core.py`
  - 출력 없음. 대상 class def 잔존 매치 없음.
- `git diff --check -- watcher_core.py watcher_state.py`
  - 통과, 출력 없음.

## 남은 리스크
- 이번 변경은 구조 이동이며 unit 테스트 묶음으로 기존 `watcher_core.*` re-export 계약을 확인했습니다. 실제 장시간 watcher runtime에서 lock/manifest 파일을 다루는 live 동작은 운영 중 자연 사용이나 별도 live smoke에서만 확인됩니다.
- docs 변경은 하지 않았습니다. 현재 shipped product contract나 사용자-facing 동작을 바꾸지 않는 내부 모듈 분리로 판단했습니다.
