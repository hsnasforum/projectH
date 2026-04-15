## 변경 파일
- pipeline_runtime/supervisor.py
- pipeline-launcher.py
- tests/test_pipeline_runtime_supervisor.py
- tests/test_pipeline_launcher.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- doc-sync

## 변경 이유
- 실제 runtime restart 후 `operator_request.md / needs_operator / seq 155`가 계속 active control로 남아 launcher 시작이 흔들리는 것처럼 보였습니다.
- 확인 결과 이 stop 문서는 `/work` blocker가 아직 미검증이라고 주장했지만, `.pipeline/state/*.json` job state에는 해당 blocker work들이 이미 `VERIFY_DONE`으로 기록되어 있었습니다.
- 즉 문제는 “실제 operator-only stop”이라기보다, stale operator stop이 control surface에서 계속 authoritative하게 남아 있던 데 있었습니다.

## 핵심 변경
- `RuntimeSupervisor`에 stale operator stop detector를 추가했습니다.
  - active control이 `.pipeline/operator_request.md`
  - stop 본문에 적힌 `work/...md` 경로들이 존재
  - 해당 work artifact들이 job state 기준 모두 `VERIFY_DONE`
  위 조건을 만족하면 supervisor가 stale operator stop으로 판단합니다.
- stale operator stop으로 판단되면:
  - runtime `status.control`은 `none`으로 내려갑니다.
  - compat/debug surface의 raw control slot에는 `operator_request.md`를 그대로 남깁니다.
  - `events.jsonl`에는 `control_operator_stale_ignored`를 기록합니다.
- launcher recent log도 `control_operator_stale_ignored verified_blockers_resolved seq=...`를 읽을 수 있게 맞췄습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline-launcher.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_launcher`
- `git diff --check -- pipeline_runtime/supervisor.py pipeline-launcher.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_launcher.py`

## 남은 리스크
- stale 여부는 현재 `operator_request.md` 본문에서 추출한 `work/...md` 경로와 job state `artifact_path` 일치로 판정합니다. stop 문구가 그 패턴을 벗어나면 suppression이 적용되지 않을 수 있습니다.
- 이번 수정은 stale stop을 authority surface에서 내리는 조치이지, 다음 exact control을 자동 생성하는 조치는 아닙니다. 최신 next control 생성은 여전히 Codex follow-up 또는 operator 결정이 필요합니다.
