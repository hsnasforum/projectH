## 변경 파일
- controller/server.py
- controller/index.html
- controller/assets/.gitkeep
- tests/test_controller_server.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- frontend-skill

## 변경 이유
- 사용자가 외부 pixel sprite sheet를 controller `Office View`에 시험 적용해 보고 싶어했습니다.
- 다만 첨부 이미지는 대화 안에서만 보이고 repo 파일로 직접 접근할 수 없어서, controller가 operator-supplied PNG를 정해진 위치에서 읽는 경로를 먼저 열어둘 필요가 있었습니다.

## 핵심 변경
- controller 서버에 `/controller-assets/<file>` 정적 자산 서빙 경로를 추가했습니다.
- `Office View`는 `controller/assets/fren-office-sheet.png`가 있으면 해당 sprite sheet를 우선 사용하고, 없으면 기존 CSS fallback avatar로 렌더링합니다.
- 현재는 사용자가 올린 시트 레이아웃을 기준으로 static crop 좌표를 미리 연결해 두었습니다.
  - `READY` → idle 계열 frame
  - `WORKING` → 공격 계열 frame
  - `BOOTING` → 점프 계열 frame
  - `BROKEN/OFF/DEAD` → grayscale fallback frame
- internal runtime 문서에도 Office View sprite 자산은 optional operator asset이며 status authority와 무관하다는 점을 반영했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server`

## 남은 리스크
- 실제 첨부 이미지 파일 자체는 아직 repo에 없으므로, 현재 브라우저에서는 fallback avatar가 계속 보일 수 있습니다.
- crop 좌표는 사용자가 올린 1280x1280 시트 레이아웃을 기준으로 잡은 추정값이어서, 실제 PNG가 약간 다르면 미세 조정이 필요할 수 있습니다.
