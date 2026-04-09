# Pipeline GUI _apply_snapshot provenance passthrough regression

## 변경 파일

- `tests/test_pipeline_gui_app.py` — provenance passthrough 회귀 2건 추가, 기존 테스트에 provenance 검증 보강

## 사용 skill

- 없음 (bounded test regression)

## 변경 이유

backend에서 `seq N` / `mtime fallback` provenance를 이미 출력하지만,
`_apply_snapshot()` 경유 app test에서 provenance 텍스트를 검증하지 않아
app 경로에서 provenance가 누락되어도 감지할 수 없었음.

## 핵심 변경

1. **`test_apply_snapshot_control_slot_seq_provenance`** (신규):
   - active에 `control_seq: 7` 포함 → `seq 7` 표시, `mtime fallback` 미표시 확인
   - stale에 `control_seq: 5` 포함 → `seq 5` 표시 확인
2. **`test_apply_snapshot_control_slot_mtime_fallback_provenance`** (신규):
   - `control_seq` 없는 active → `mtime fallback` 표시, `seq ` 미표시 확인
3. **기존 `test_apply_snapshot_control_slot_normal_active`** 보강:
   - active/stale 모두 `mtime fallback` 포함 검증 추가 (기존 color 검증과 함께)

## 검증

```
python3 -m unittest -v tests.test_pipeline_gui_app  # 29/29 OK
python3 -m py_compile pipeline_gui/app.py            # OK
git diff --check                                     # clean
```

## 남은 리스크

- backend 파싱 로직, watcher 런타임, guide 텍스트, system-card 레이아웃은 이번 라운드에서 변경하지 않음
- `_make_snapshot_gui()` stub은 app.py attribute 추가 시 갱신 필요
