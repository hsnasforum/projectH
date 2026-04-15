## 변경 파일
- controller/index.html
- tests/test_controller_server.py

## 사용 skill
- frontend-skill

## 변경 이유
- Office View가 이전 sprite-sheet 좌표를 계속 사용하고 있어, 사용자가 새로 교체한 `fren-office-sheet.png` 레이아웃과 맞지 않았습니다.
- 새 시트는 `READY / WORKING / BOOTING / BROKEN / attachable false / dead`가 한 장 안에 재배치되어 있어 상태별 clip 범위를 다시 잡아야 했습니다.

## 핵심 변경
- `controller/index.html`의 `OFFICE_SPRITE_ANIMATIONS`를 새 2715x1358 sprite sheet 기준으로 다시 매핑했습니다.
- `dead` 상태를 별도 animation row로 추가하고, `off` 상태는 `dead` row를 사용하도록 바꿨습니다.
- sprite image cache-bust 버전을 `office-sprite-v3`로 올려, 같은 파일명 교체 시 브라우저가 이전 frame cache를 잡고 있지 않게 했습니다.

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
- 새 clip 좌표는 실제 시트 기준으로 재조정했지만, Office View 레이아웃 안에서 더 크게/작게 보이길 원하시면 sprite display scale은 추가 미세조정이 필요할 수 있습니다.
- source PNG는 여전히 설명 문구와 checker background가 있는 시트라, 완전한 전용 sprite-sheet보다는 품질 한계가 있습니다.
