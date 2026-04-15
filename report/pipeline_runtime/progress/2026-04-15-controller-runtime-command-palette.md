## 변경 파일
- controller/index.html
- tests/test_controller_server.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- doc-sync

## 변경 이유
- 브라우저 controller에서 start/stop/restart/attach 같은 operator 작업을 버튼 외에도 바로 타이핑해 실행하고 싶은 요구가 있었습니다.
- 다만 internal tooling이라도 arbitrary shell exec를 열면 runtime 문서 경계와 safety 원칙을 무너뜨리므로, bounded command palette 형태가 필요했습니다.

## 핵심 변경
- controller right panel에 typed runtime command palette를 추가했습니다.
- 허용 명령은 기존 controller HTTP API에 매핑되는 bounded set으로만 제한했습니다.
  - `start`
  - `stop`
  - `restart`
  - `attach [Claude|Codex|Gemini]`
  - `tail <Claude|Codex|Gemini> [lines]`
  - `view <all|Claude|Codex|Gemini>`
  - `text <on|off> [lines]`
  - `status`
  - `help`
- 새 backend exec endpoint는 추가하지 않았고, 브라우저는 계속 `/api/runtime/status`, `/api/runtime/start|stop|restart`, `/api/runtime/attach`, `/api/runtime/capture-tail`만 사용합니다.
- focus mode에서도 right panel을 숨기지 않도록 바꿔 command palette가 항상 보이게 했습니다.
- runtime docs에 browser controller typed command palette가 arbitrary shell이 아니라는 경계를 짧게 반영했습니다.

## 검증
- `node - <<'JS' ... new Function(script) ... JS`
- `python3 -m unittest -v tests.test_controller_server`

## 남은 리스크
- command palette는 operator UX layer일 뿐이므로, status truth와 recovery 판단은 계속 supervisor status/events에 의존해야 합니다.
- right panel 폭이 넓어져 center pane 가로폭이 조금 줄었습니다. 필요하면 후속으로 collapsible command palette로 더 다듬을 수 있습니다.
