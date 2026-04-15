## 변경 파일
- controller/index.html
- tests/test_controller_server.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- frontend-skill

## 변경 이유
- 기존 Office View sprite 적용은 static single-frame crop이라 흰 배경 박스가 그대로 보이고 움직임이 부자연스러웠습니다.
- 사용자가 더 자연스러운 움직임과 배경 정리를 원해 controller browser 쪽 read-model sprite 처리 품질을 높일 필요가 있었습니다.

## 핵심 변경
- `Office View`를 static crop에서 state별 multi-frame animation으로 바꿨습니다.
  - `READY`는 idle 4프레임
  - `WORKING`은 magic-cast 4단계
  - `BOOTING`은 jump 4프레임
  - `BROKEN/OFF/DEAD`는 reverse-walk 계열 + grayscale
- controller browser가 sprite sheet를 client-side로 잘라내면서 frame 가장자리의 연결된 white background를 trim하도록 했습니다.
- trim 뒤에 opaque bounds를 다시 잘라내어, 이전처럼 큰 흰 직사각형이 통째로 보이지 않도록 줄였습니다.
- sprite frame은 runtime poll과 분리된 짧은 interval로 갱신해 더 자연스러운 움직임처럼 보이게 했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server`
- `python3 - <<'PY' >/tmp/projecth-controller-office.js
from pathlib import Path
html = Path('controller/index.html').read_text(encoding='utf-8')
start = html.index('<script>') + len('<script>')
end = html.rindex('</script>')
print(html[start:end])
PY
node --check /tmp/projecth-controller-office.js`

## 남은 리스크
- 현재 소스 PNG 자체가 설명용 흰 배경 시트라, 완전한 transparent sprite 품질은 한계가 있습니다.
- frame clip은 현재 실제 시트 레이아웃에 맞춰 수동 고정되어 있어, 다른 sprite sheet로 교체하면 clip 재조정이 필요합니다.
