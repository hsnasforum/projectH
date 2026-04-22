# 2026-04-23 Milestone 12 Axis 4 promote assets

## 변경 파일
- `scripts/promote_assets.py`
- `tests/test_promote_assets.py`
- `work/4/23/2026-04-23-milestone12-axis4-promote-assets.md`

## 사용 skill
- `security-gate`: high-quality trace를 읽어 `data/corrections/`에 promoted correction asset을 쓰는 변경이므로 로컬 파일 쓰기 위치와 원본 session JSON 비수정 경계를 확인했습니다.
- `finalize-lite`: handoff가 요구한 컴파일, unittest, export, promotion 실행 결과만 기준으로 완료 여부를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 명령, 남은 리스크를 한국어 closeout으로 남겼습니다.

## 변경 이유
- Milestone 12 Axis 4 handoff(`CONTROL_SEQ: 934`)에 따라 `data/high_quality_traces.jsonl`의 high-quality correction pair를 `CorrectionStore` personalization asset으로 승격해야 했습니다.
- 기존 `CorrectionStore.record_correction()`과 `promote_correction()` 인프라를 재사용해 storage contract 변경 없이 asset promotion CLI를 추가했습니다.

## 핵심 변경
- `scripts/promote_assets.py`를 추가해 `data/high_quality_traces.jsonl`을 읽고 각 pair를 `CorrectionStore.record_correction()` 후 `promote_correction()`으로 `CorrectionStatus.PROMOTED` 상태까지 전환하도록 했습니다.
- missing high-quality trace file은 `main()`에서 안내 메시지를 출력하고 정상 종료하도록 했습니다.
- `tests/test_promote_assets.py`를 추가해 promotion 저장, idempotent 재실행, missing-file main guard를 검증했습니다.
- `session_store.py`, `agent_loop.py`, storage contract, frontend는 handoff 범위 밖이라 수정하지 않았습니다.

## 검증
- `python3 -m py_compile scripts/promote_assets.py tests/test_promote_assets.py`
  - 통과
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets -v 2>&1 | tail -5`
  - `Ran 49 tests in 0.046s`
  - `OK`
- `python3 scripts/export_traces.py`
  - `Exported 137 correction pairs → data/all_traces.jsonl`
  - `High-quality pairs: 137 → data/high_quality_traces.jsonl`
- `python3 scripts/promote_assets.py`
  - `Promoted 137 correction pairs → data/corrections/ (0 skipped)`
- `ls data/corrections | wc -l`
  - `8021`

## 남은 리스크
- 실제 `data/corrections/`에 이미 많은 correction record가 있어 promotion 실행은 다소 오래 걸렸습니다. 이번 slice는 handoff대로 script/test 추가만 수행했고, `CorrectionStore` 성능 개선이나 별도 색인은 변경하지 않았습니다.
- promotion asset 품질 검토, feedback metadata 결합, Axis 5 이후 활용 흐름은 이번 범위가 아닙니다.
- `data/corrections/`, `data/all_traces.jsonl`, `data/high_quality_traces.jsonl`은 로컬 산출물이며 현재 `git status --short`에는 나타나지 않았습니다.
