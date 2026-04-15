## 변경 파일
- scripts/build_office_sprites.py
- controller/index.html
- tests/test_controller_server.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md
- controller/assets/generated/ready-00.png
- controller/assets/generated/ready-01.png
- controller/assets/generated/ready-02.png
- controller/assets/generated/ready-03.png
- controller/assets/generated/working-00.png
- controller/assets/generated/working-01.png
- controller/assets/generated/working-02.png
- controller/assets/generated/working-03.png
- controller/assets/generated/booting-00.png
- controller/assets/generated/booting-01.png
- controller/assets/generated/booting-02.png
- controller/assets/generated/booting-03.png
- controller/assets/generated/broken-00.png
- controller/assets/generated/broken-01.png
- controller/assets/generated/broken-02.png
- controller/assets/generated/broken-03.png
- controller/assets/generated/dead-00.png
- controller/assets/generated/dead-01.png
- controller/assets/generated/dead-02.png
- controller/assets/generated/dead-03.png
- controller/assets/generated/office-sprite-manifest.json

## 사용 skill
- frontend-skill

## 변경 이유
- 브라우저에서 raw sprite sheet를 직접 crop/trim 하던 방식만으로는 프레임 크기 점프와 딱딱한 움직임을 충분히 줄이기 어려웠습니다.
- 사용자가 `Pillow` 기반 사전 가공 예시를 주었고, Office View를 prebuilt normalized frame 파이프라인으로 옮기는 쪽이 더 자연스럽고 유지보수 가능하다고 판단했습니다.

## 핵심 변경
- `scripts/build_office_sprites.py`를 추가해 `controller/assets/fren-office-sheet.png`에서 상태별 프레임을 추출하고, edge whitespace trim + bottom-anchor normalization을 거친 PNG frame set과 manifest를 생성하도록 했습니다.
- controller는 이제 `controller/assets/generated/office-sprite-manifest.json`가 있으면 generated frame 세트를 우선 사용하고, 없을 때만 raw sheet fallback 경로를 사용합니다.
- generated manifest에는 상태별 `interval_ms`, `sequence`, frame URL/size가 들어 있어 browser는 crop 없이 재생만 담당합니다.
- 실제 current sprite sheet 기준 generated frame set을 한 번 생성해 `controller/assets/generated/` 아래에 배치했습니다.

## 검증
- `python3 scripts/build_office_sprites.py`
- `python3 -m py_compile scripts/build_office_sprites.py controller/server.py tests/test_controller_server.py`
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
- 현재 source sprite sheet 자체가 설명 텍스트와 체크 배경을 포함한 합성 자산이어서, generated frame도 전용 게임용 spritesheet만큼 완벽하진 않습니다.
- 사용자가 원본 sheet를 다시 교체하면 `python3 scripts/build_office_sprites.py`를 다시 실행해 generated frame set을 갱신해야 합니다.
