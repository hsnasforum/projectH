## 변경 파일
- controller/index.html
- tests/test_controller_server.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- frontend-skill

## 변경 이유
- Office View에서 프리렌 sprite가 프레임마다 미세하게 커졌다 작아져 보였고, 4컷 루프가 `1-2-3-4-1`로 바로 되감기며 끊기는 느낌이 있었습니다.
- 사용자는 캐릭터 크기 일관성과 더 자연스러운 움직임을 원했습니다.

## 핵심 변경
- sprite frame을 browser에서 바로 표시하지 않고, 상태별 animation frame을 한 번 더 동일 viewport로 정규화해 캐릭터 크기 점프를 줄였습니다.
- animation loop를 `ping-pong` sequence로 바꿔 `1-2-3-4-3-2` 계열로 왕복하도록 했습니다.
- frame 교체는 단일 img 교체 대신 2-layer crossfade로 바꿔 전환 순간의 딱딱한 끊김을 줄였습니다.
- cache-bust marker를 `office-sprite-v4`로 올려 새 모션 파라미터가 브라우저에 즉시 반영되도록 했습니다.

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
- source sprite sheet가 설명 문구와 checker 배경을 포함한 시트라, 전용 게임용 sprite sheet만큼 매끈한 보간 품질에는 한계가 있습니다.
- WORKING row처럼 효과 이펙트가 큰 프레임은 body 기준은 안정돼도 effect 범위 때문에 넓이가 바뀌는 느낌이 일부 남을 수 있습니다.
