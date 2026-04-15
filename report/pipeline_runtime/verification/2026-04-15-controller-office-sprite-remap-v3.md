# 2026-04-15 controller office sprite remap v3 verification

## 검증 범위
- `controller/index.html`
- `tests/test_controller_server.py`

## 실행한 검증
- `python3 -m unittest -v tests.test_controller_server`
- `python3 - <<'PY' >/tmp/projecth-controller-office.js
from pathlib import Path
html = Path('controller/index.html').read_text(encoding='utf-8')
start = html.index('<script>') + len('<script>')
end = html.rindex('</script>')
print(html[start:end])
PY
node --check /tmp/projecth-controller-office.js`

## 결과
- controller server 테스트가 통과했습니다.
- controller HTML에 새 sprite cache-bust marker(`office-sprite-v3`)가 반영되어 있음을 확인했습니다.
- 추출한 browser script는 `node --check`를 통과했습니다.

## 해석
- 이제 Office View는 사용자가 교체한 최신 `fren-office-sheet.png` 레이아웃 기준으로 `READY / WORKING / BOOTING / BROKEN / DEAD`를 다시 읽습니다.
- 같은 파일명으로 sprite sheet를 교체해도 이전 frame cache가 남아 보이는 문제를 줄였습니다.

## 메모
- 사용자는 브라우저에서 강새로고침(`Ctrl+Shift+R`) 후 결과를 확인하는 편이 좋습니다.
