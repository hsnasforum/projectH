# 2026-04-15 office view pillow prebuild pipeline verification

## 검증 범위
- `scripts/build_office_sprites.py`
- `controller/index.html`
- `tests/test_controller_server.py`
- `controller/assets/generated/*`

## 실행한 검증
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

## 결과
- generated frame 20개와 `office-sprite-manifest.json`이 실제로 생성되었습니다.
- manifest에는 `frame_box = 220x190`, 상태별 `interval_ms`, `sequence`, frame URL/size가 정상 기록되어 있습니다.
- controller server 테스트가 통과했고, controller HTML 스크립트도 문법 검사를 통과했습니다.

## 해석
- Office View는 이제 Pillow로 정규화된 sprite frame 세트를 우선 사용하므로, raw sheet crop 기반일 때보다 프레임별 크기 점프를 줄일 수 있습니다.
- 브라우저는 여전히 ping-pong/crossfade를 적용하지만, 이제 그 대상이 prebuilt normalized frame이어서 체감 품질이 더 안정적입니다.

## 메모
- source sheet가 바뀌면 `python3 scripts/build_office_sprites.py`를 다시 실행해야 generated frame set이 갱신됩니다.
