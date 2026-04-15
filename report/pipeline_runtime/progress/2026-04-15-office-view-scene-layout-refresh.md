# 2026-04-15 office view scene layout refresh

## 요약
- 기존 Office View는 agent 3장을 카드처럼 병렬 배치하는 느낌이 강해서 `claude-office` 계열의 “한 공간 안에서 함께 일하는 장면” 분위기와 거리가 있었습니다.
- 이번 수정으로 Office View를 scene-first 레이아웃으로 바꿔, 한 개의 dark office room 안에 Claude / Codex / Gemini 책상을 고정 배치하고 우측 inspector를 분리했습니다.

## 변경 파일
- `controller/index.html`

## 핵심 변경
- 상단 summary는 유지하되, 본문은 `office-shell = office room + inspector` 2단 구조로 재배치했습니다.
- 중앙 room에는 window band, ambient glow, floor depth를 넣고 3개 desk를 absolute scene position으로 고정했습니다.
- agent 상태는 desk glow / sprite motion / bubble / state pill로 보이게 했고, runtime detail은 우측 inspector로 분리했습니다.
- `READY.gif`와 기존 sprite sheet/generated frame 경로는 그대로 유지하면서 장면 배치만 바꿨습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server`
- `git diff --check -- controller/index.html`

## 메모
- 이번 변경은 visual read-model 개편이며 runtime authority나 controller API 계약은 바꾸지 않았습니다.
- 더 `claude-office`에 가깝게 가려면 다음 단계에서 desk 간 이동, watcher 오브젝트, 이벤트 기반 이펙트 같은 scene behavior를 추가할 수 있습니다.
