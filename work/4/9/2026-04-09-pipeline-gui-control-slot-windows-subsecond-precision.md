# Pipeline GUI control-slot Windows/WSL sub-second mtime precision

## 변경 파일

- `pipeline_gui/backend.py` — `stat -c %Y` → `stat -c %Y.%N` (sub-second precision)
- `tests/test_pipeline_gui_backend.py` — same-second collision 회귀 + Windows branch mock 테스트 추가

## 사용 skill

- 없음 (bounded precision fix)

## 변경 이유

Windows/WSL 경로에서 `stat -c %Y`는 정수 초만 반환하여, 같은 초 안에 control slot이 재작성되면
newest-valid-control 선택이 틀릴 수 있었음. sub-second precision으로 전환하여 정확한 순서를 보장.

## 핵심 변경

1. **`pipeline_gui/backend.py`**: Windows path의 `stat -c %Y` → `stat -c %Y.%N`
   - GNU coreutils `stat`에서 `%Y.%N`는 `epoch.nanoseconds` 형식으로 sub-second 정밀도 제공
   - `float()` 파싱은 기존과 동일하게 동작
2. **`tests/test_pipeline_gui_backend.py`**:
   - `test_same_second_mtime_uses_subsecond_precision`: 같은 정수 초 내에서 0.1초 vs 0.9초 차이로 정확한 active 선택 확인
   - `TestParseControlSlotsWindowsBranch.test_windows_stat_uses_subsecond_format`: IS_WINDOWS mock으로 `_run(["stat", ...])` 경로를 직접 검증, sub-second mtime 파싱 확인

## 검증

```
python3 -m unittest -v tests.test_pipeline_gui_backend  # 12/12 OK
python3 -m py_compile pipeline_gui/backend.py            # OK
git diff --check                                         # clean
```

## 남은 리스크

- `%N` 지원은 GNU coreutils 8.x+ 기준이며, WSL Ubuntu 기본 설치에서 사용 가능
- 매우 오래된 busybox stat에서는 `%N`이 없을 수 있으나, WSL 환경에서는 해당 없음
- watcher 런타임 동작, system-card 레이아웃, guide 텍스트는 이번 라운드에서 변경하지 않음
