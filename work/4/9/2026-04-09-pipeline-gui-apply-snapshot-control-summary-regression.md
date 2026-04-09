# Pipeline GUI _apply_snapshot control-summary wiring regression

## 변경 파일

- `tests/test_pipeline_gui_app.py` — `_apply_snapshot()` 경유 control-slot 통합 회귀 3건 추가, `_Widget` fg/bg 추적 보강, `_make_snapshot_gui()` / `_base_snapshot()` 헬퍼 추가

## 사용 skill

- 없음 (bounded test regression)

## 변경 이유

이전 control-slot 테스트(`test_apply_snapshot_sets_control_slot_vars`)는 `_apply_snapshot()`을 호출하지 않고
var에 직접 값을 넣어 검증했으므로, 실제 app 경로의 wiring이나 active-label 색상 로직 회귀를 감지하지 못했음.

## 핵심 변경

1. **`_Widget` 보강**: `configure(fg=..., bg=...)` 호출 시 `_fg`, `_bg` 속성에 기록하여 색상 검증 가능
2. **`_make_snapshot_gui()`**: `_apply_snapshot()`을 실행할 수 있는 최소한의 PipelineGUI stub 생성
3. **`_base_snapshot()`**: 유효한 minimal snapshot dict 생성
4. **회귀 테스트 3건** (모두 `_apply_snapshot()` 실제 호출):
   - `test_apply_snapshot_control_slot_normal_active`: 일반 active → 파란색(`#60a5fa`), stale 표시에 `비활성` 포함
   - `test_apply_snapshot_control_slot_needs_operator_red`: `needs_operator` active → 빨간색(`#f87171`)
   - `test_apply_snapshot_control_slot_no_active_gray`: active 없음 → 회색(`#6b7280`), `활성 제어: 없음`

## 검증

```
python3 -m unittest -v tests.test_pipeline_gui_app  # 27/27 OK
python3 -m py_compile pipeline_gui/app.py            # OK
git diff --check                                     # clean
```

## 남은 리스크

- `_make_snapshot_gui()`는 `_apply_snapshot()`의 현재 attribute 접근에 맞춘 stub이므로, app.py에 새 attribute가 추가되면 갱신 필요
- backend 파싱 로직, watcher 런타임, guide 텍스트, system-card 레이아웃은 이번 라운드에서 변경하지 않음
