# 2026-04-15 stale operator stop suppression verification

## 검증 범위
- `pipeline_runtime/supervisor.py`
- `pipeline-launcher.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_launcher.py`
- runtime stale-operator-stop read model

## 실행한 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline-launcher.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_launcher`
- live truth inspection:
  - `.pipeline/operator_request.md`
  - `.pipeline/state/*.json`
  - current run `status.json`
  - current run `events.jsonl`

## 결과
- `py_compile` 통과
- `tests.test_pipeline_runtime_supervisor` + `tests.test_pipeline_launcher` 통과
- live inspection에서 아래를 확인했습니다.
  - active stop 문서 `seq 155`는 `review-queue` blocker `/work`가 미검증이라고 서술하고 있었음
  - 그러나 `.pipeline/state`의 corresponding job state에는 해당 blocker work들이 이미 `VERIFY_DONE`으로 남아 있었음
  - stale operator stop을 무조건 authority로 유지하면 launcher/controller가 operator wait를 truth처럼 오래 surface할 수 있음

## 해석
- 이번 수정으로 supervisor는 stale operator stop을 debug surface로는 남기되, current runtime control truth로는 승격하지 않게 됩니다.
- `control_operator_stale_ignored` event가 생기므로 operator는 “stop 파일이 있다”와 “지금도 실제 stop이어야 한다”를 구분할 수 있습니다.
- 이 조치는 runtime surface truth 안정화용이며, 다음 exact control 자동 생성과는 별개입니다.

## 메모
- stale operator stop suppression은 duplicate handoff suppression과 같은 계열의 read-model normalization입니다.
- `.pipeline/operator_request.md` 파일을 자동 삭제하거나 rewrite하지는 않습니다.
