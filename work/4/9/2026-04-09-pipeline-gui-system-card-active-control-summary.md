# Pipeline GUI system-card active control / inactive stale summary

## 변경 파일

- `pipeline_gui/backend.py` — `parse_control_slots()`, `format_control_summary()` 신규 helper
- `pipeline_gui/app.py` — snapshot에 control_slots 추가, _apply_snapshot에서 시스템 카드에 반영
- `pipeline_gui/view.py` — 시스템 카드에 `활성 제어:` / `비활성:` label 추가
- `tests/test_pipeline_gui_backend.py` — 신규: control slot 파싱 및 포맷 테스트 8개
- `tests/test_pipeline_gui_app.py` — control slot system-card 렌더링 테스트 1개 추가
- `windows-launchers/README.md` — 활성 제어 visibility 문서 추가

## 사용 skill

- 없음 (bounded operator-tooling 슬라이스)

## 변경 이유

launcher `시스템` 카드에 현재 어떤 control 슬롯이 활성인지, 어떤 것이 비활성(stale)인지 표시하지 않아
operator가 실제 dispatch 상태를 launcher에서 확인할 수 없었음.
guide 텍스트에 newest-valid-control 의미론이 반영된 이후, 실제 시스템 카드에도 같은 정보를 보여주는 것이 자연스러운 후속.

## 핵심 변경

1. **backend helper** (`pipeline_gui/backend.py`):
   - `parse_control_slots(project)`: 4개 canonical control slot을 읽고 STATUS 검증 후 mtime 기준으로 newest valid → active, 나머지 → stale로 분류
   - `format_control_summary(parsed)`: active/stale 정보를 시스템 카드 표시용 텍스트로 변환
2. **snapshot/apply** (`pipeline_gui/app.py`):
   - `_build_snapshot`에 `control_slots` 추가
   - `_apply_snapshot`에서 `활성 제어:` / `비활성:` var 갱신 + operator_request active일 때 빨간색 표시
3. **시스템 카드 UI** (`pipeline_gui/view.py`):
   - `활성 제어:` label (파란색 기본, operator stop 시 빨간색)
   - `비활성:` label (회색)
4. **테스트**:
   - `test_pipeline_gui_backend.py`: active selection, newest wins, invalid status exclusion, multiple stale, format rendering (8 tests)
   - `test_pipeline_gui_app.py`: system-card var rendering (1 test)
5. **문서**: `windows-launchers/README.md`에 활성 제어 visibility 설명 추가

## 검증

```
python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_pipeline_gui_app  # 33/33 OK
python3 -m py_compile pipeline_gui/backend.py pipeline_gui/app.py pipeline_gui/view.py  # OK
git diff --check  # clean
```

## 남은 리스크

- 읽기 전용 표시만 추가했으며 slot mutation이나 watcher 런타임 변경 없음
- system-card 전체 리디자인, TUI, setup-mode 연동은 별도 슬라이스
- Windows WSL 경로에서 `stat -c %Y` fallback은 기존 `_run` 패턴과 동일
