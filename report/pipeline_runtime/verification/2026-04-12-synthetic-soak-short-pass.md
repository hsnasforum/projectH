# 2026-04-12 synthetic soak short pass

## 변경 파일
- [pipeline_runtime/supervisor.py](/home/xpdlqj/code/projectH/pipeline_runtime/supervisor.py)
- [scripts/pipeline_runtime_gate.py](/home/xpdlqj/code/projectH/scripts/pipeline_runtime_gate.py)
- [scripts/pipeline_runtime_fake_lane.py](/home/xpdlqj/code/projectH/scripts/pipeline_runtime_fake_lane.py)
- [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py)
- [tests/test_pipeline_runtime_gate.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_gate.py)
- [tests/test_pipeline_runtime_fake_lane.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_fake_lane.py)

## 사용 skill
- 없음

## 변경 이유
- 장시간 채택 게이트 전에 real repo `work/verify`를 오염시키지 않는 공식 synthetic soak 경로가 필요했습니다.

## 핵심 변경
- `supervisor`에 lane command override seam과 tmux pane용 `PYTHONPATH` 전달을 추가했습니다.
- `scripts/pipeline_runtime_fake_lane.py`를 추가해 synthetic Claude/Codex/Gemini lane이 temp workspace 안에서 `/work`, `/verify`, `.pipeline/*.md`, `report/gemini/`를 실제로 쓰도록 했습니다.
- `scripts/pipeline_runtime_gate.py synthetic-soak`가 temp workspace를 만들고 `receipt_count`, `duplicate_dispatch_count`, `control_mismatch_samples`, `control_mismatch_max_streak`, `orphan_session`를 함께 보고하도록 보강했습니다.
- short synthetic soak에서 첫 receipt까지 닫히는 것을 확인했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py scripts/pipeline_runtime_gate.py scripts/pipeline_runtime_fake_lane.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_gate.py tests/test_pipeline_runtime_fake_lane.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_gate tests.test_pipeline_runtime_fake_lane`
- `python3 scripts/pipeline_runtime_gate.py --mode experimental synthetic-soak --duration-sec 30 --sample-interval-sec 1 --min-receipts 1 --report /tmp/projecth-synthetic-soak-smoke.md`
  - 요약: `receipt_count=1`, `duplicate_dispatch_count=0`, `control_mismatch_max_streak=1`, `orphan_session=False`, `broken_seen=False`

## 남은 리스크
- 아직 30초 short synthetic soak만 확인했고, 문서상 채택 게이트인 6h / 24h synthetic soak는 남아 있습니다.
- current `control_mismatch_samples=1`은 transition 창에서만 관측됐고 persistent mismatch는 아니었지만, 장시간 soak에서 반복 양상을 다시 봐야 합니다.
