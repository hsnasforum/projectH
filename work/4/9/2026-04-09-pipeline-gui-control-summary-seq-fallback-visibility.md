# Pipeline GUI control-summary seq/fallback visibility

## 변경 파일

- `pipeline_gui/backend.py` — `format_control_summary()` 출력에 `seq N` / `mtime fallback` provenance 표시 추가
- `tests/test_pipeline_gui_backend.py` — provenance 관련 테스트 3건 추가 (seq 표시, mtime fallback 표시, mixed provenance stale)

## 사용 skill

- 없음 (bounded display enhancement)

## 변경 이유

`CONTROL_SEQ` 기반 newest-valid-control 정렬이 도입되었지만, launcher 시스템 카드에서
active/stale 제어 슬롯이 `CONTROL_SEQ`로 선택되었는지 `mtime` fallback으로 선택되었는지
operator가 구분할 수 없었음. 수동/out-of-band 제어 파일 작성자가 `CONTROL_SEQ` 누락을
진단할 수 있도록 provenance를 표시.

## 핵심 변경

1. **`_slot_provenance(entry)`** 신규 helper: `control_seq`가 있으면 `seq N`, 없으면 `mtime fallback` 반환
2. **`format_control_summary()`**: active/stale 텍스트에 provenance 포함
   - active: `활성 제어: Claude 실행 (claude_handoff.md, seq 5)`
   - stale: `비활성: operator_request.md (seq 2), gemini_request.md (mtime fallback)`
3. **테스트**:
   - `test_active_with_control_seq_shows_seq`: seq가 있을 때 `seq N` 표시, `mtime fallback` 미표시
   - `test_stale_with_mixed_provenance`: mixed seq/mtime stale 항목 각각 올바른 provenance
   - 기존 `test_active_with_stale`: `mtime fallback` 표시 검증 추가

## 검증

```
python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_pipeline_gui_app  # 42/42 OK
python3 -m py_compile pipeline_gui/backend.py pipeline_gui/app.py                   # OK
git diff --check                                                                     # clean
```

## 남은 리스크

- provenance 텍스트가 카드 폭을 약간 넓힐 수 있으나 현재 레이아웃에서 충분히 수용 가능
- watcher 런타임 동작, guide 텍스트, system-card 레이아웃은 이번 라운드에서 변경하지 않음
