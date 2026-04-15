# 2026-04-15 office view sprite motion smoothing verification

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
- controller HTML에 `office-sprite-v4`, `buildOfficeAnimationFrames`, `office-sprite-layers`가 반영되어 sprite normalization/crossfade 경로가 들어갔음을 확인했습니다.
- 추출한 browser script는 `node --check`를 통과했습니다.

## 해석
- Office View는 이제 프레임마다 다른 crop 크기를 그대로 쓰지 않고 동일 viewport로 정규화해 표시합니다.
- animation loop는 hard reset 대신 ping-pong sequence로 돌고, frame 전환은 crossfade로 처리되어 이전보다 덜 딱딱하게 보이는 방향입니다.

## 메모
- 최종 시각 품질은 실제 브라우저에서 강새로고침 후 체감 확인이 필요합니다.
