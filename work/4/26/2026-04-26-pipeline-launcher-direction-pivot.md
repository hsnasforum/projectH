# 2026-04-26 pipeline launcher 방향 전환

## 변경 파일
- `.pipeline/operator_request.md` (gitignored local control slot): M44 publish gate를 operator 지시에 따라 superseded 처리
- `.pipeline/implement_handoff.md` (gitignored local control slot): pipeline launcher non-operator hibernate surface slice로 active control 전환
- `work/4/26/2026-04-26-pipeline-launcher-direction-pivot.md`

## 사용 skill
- `onboard-lite`: pipeline launcher 관련 최근 work/verify, 런처 entrypoint, test entrypoint, runtime status truth를 좁게 확인했다.
- `security-gate`: 런처/supervisor shell runtime 표면을 다루므로, 변경 범위를 표시/컨트롤 라우팅에 한정하고 publish/approval semantics를 넓히지 않는지 점검했다.
- `work-log-closeout`: operator 방향 전환과 실제 확인 결과를 한국어 closeout으로 남겼다.

## 변경 이유
- 사용자가 M44 publish 흐름 대신 멈춰 있는 pipeline launcher 쪽 개발로 방향 전환을 명시했다.
- live status는 `RUNNING`, lanes `READY`, canonical control `none`, `automation_health = ok`였지만, `autonomy.mode = hibernate`와 compat `operator_request.md`가 함께 남아 있어 런처/컨트롤러 표면에서 멈춘 operator wait처럼 보일 수 있었다.
- 따라서 M44 publish gate는 보류하고, launcher가 canonical status와 compat debug slot을 구분해 표시하는 작은 구현 slice로 전환했다.

## 핵심 변경
- `.pipeline/operator_request.md` CONTROL_SEQ 285 `m44_publish_pr_creation_merge`를 `STATUS: superseded`로 바꿔 active operator slot에서 내렸다.
- `.pipeline/implement_handoff.md` CONTROL_SEQ 286을 새로 작성해 pipeline launcher non-operator hibernate surface 구현을 active slice로 지정했다.
- 구현 범위는 `pipeline-launcher.py`와 `tests/test_pipeline_launcher.py` 우선이며, controller JS는 실제 drift가 있을 때만 좁게 수정하도록 제한했다.
- M44 2커밋 publish는 defer 상태이며 거절하거나 publish하지 않았다.

## 검증
- `python3 -m pipeline_runtime.cli status . --json` 실행: runtime `RUNNING`, lanes `READY`, canonical control `none`, `automation_health = ok`, `autonomy.mode = hibernate`, `operator_eligible = false`, compat active `operator_request.md` 확인.
- `python3`로 `pipeline_runtime.schema.parse_control_slots(Path(".pipeline"))` 실행 전 active가 `operator_request.md` CONTROL_SEQ 285임을 확인했다.
- `sed`/`rg`로 `.pipeline/README.md`, `pipeline-launcher.py`, `tests/test_pipeline_launcher.py`, `controller/js/cozy.js`의 launcher/controller status 표시 경계를 확인했다.
- 코드 구현과 unit/browser 검증은 아직 실행하지 않았다. 새 active implement handoff가 다음 구현 라운드에서 수행해야 한다.

## 남은 리스크
- M44 publish gate는 보류됐으므로 `origin/main`에는 아직 M44 2커밋이 들어가지 않았다.
- 이번 라운드는 방향 전환/컨트롤 정리이며 launcher 코드 수정 자체는 다음 implement handoff의 책임이다.
- 기존 untracked `report/gemini/**`, 이전 PR36/PR37 closeout/verify notes는 이번 방향 전환 범위 밖이다.
