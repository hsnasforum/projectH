# Pipeline GUI Windows control-slot find -printf mtime fix

## 변경 파일

- `pipeline_gui/backend.py` — Windows mtime 수집을 `stat -c %Y.%N` → `find -printf '%T@'`로 교체
- `tests/test_pipeline_gui_backend.py` — Windows branch mock을 실제 `find` 출력 형식으로 교체, same-second fractional 회귀 추가

## 사용 skill

- 없음 (bounded precision repair)

## 변경 이유

이전 라운드에서 `stat -c %Y.%N`을 사용했으나, GNU stat의 `%N`은 나노초가 아니라 "quoted file name"이므로
실제 WSL에서 `1712700000.'/path/to/file'` 형태를 반환하여 `float()` 파싱이 실패했음.
기존 codebase의 `latest_md()`가 이미 `find -printf '%T@'`로 sub-second epoch float를 안정적으로 수집하는
패턴을 사용하고 있어 같은 방식으로 통일.

## 핵심 변경

1. **`pipeline_gui/backend.py`**: Windows path의 mtime 수집을 `stat -c %Y.%N` → `find <path> -maxdepth 0 -printf '%T@\n'`으로 교체
   - `find -printf '%T@'`는 `1712700000.5000000000` 같은 정확한 epoch float를 반환
   - `latest_md()`에서 이미 검증된 동일 패턴 재사용
2. **`tests/test_pipeline_gui_backend.py`**:
   - `test_windows_find_printf_produces_subsecond_mtime`: `find` 기반 mock으로 교체, 실제 출력 형식(`1712700000.5000000000\n`) 반영
   - `test_windows_find_same_second_resolved_by_fractional`: 같은 정수 초 내에서 fractional 차이로 올바른 active 선택 확인 (신규)
3. **CONTROL_SEQ 우선 / mtime 보조 정렬**: 이전 라운드에서 추가된 watcher-aligned 정렬 로직은 유지 (watcher_core.py와 일관)

## 검증

```
python3 -m unittest -v tests.test_pipeline_gui_backend  # 13/13 OK
python3 -m py_compile pipeline_gui/backend.py            # OK
git diff --check                                         # clean
```

## 남은 리스크

- watcher 런타임 동작, system-card 레이아웃, guide 텍스트는 이번 라운드에서 변경하지 않음
- `find -maxdepth 0 -printf '%T@'`는 GNU find 기준이며 WSL Ubuntu에서 지원됨
- 실제 Windows .exe launcher 환경에서의 end-to-end 확인은 별도 수동 검증 필요
