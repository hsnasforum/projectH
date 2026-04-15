## 변경 파일
- controller/index.html

## 사용 skill
- 없음

## 변경 이유
- controller의 `텍스트 ON` debug tail이 터미널용 공백/들여쓰기를 그대로 보여 주면서 왼쪽으로 몰려 보이고, pane의 가로 공간을 충분히 활용하지 못했습니다.

## 핵심 변경
- pane-body의 좌우 padding을 줄이고 line-height를 약간 조정해 동일 폭에서 더 많은 텍스트가 보이게 했습니다.
- `word-break: break-all`을 제거해 단어/토큰이 과하게 조각나지 않도록 했습니다.
- 브라우저 표시 전용 `normalizeTailText()`를 추가해:
  - 앞뒤 빈 줄 제거
  - 연속 빈 줄 1개로 축소
  - 큰 leading indent를 2칸 수준으로 완화
  - trailing whitespace 제거
  - blank 기준 블록 안에서 terminal width 때문에 잘린 continuation line을 문장 단위로 다시 이어 붙이는 reflow
  를 적용했습니다.
- runtime status나 capture-tail API 원문은 바꾸지 않고, controller 렌더링에서만 compact view를 적용했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server`

## 남은 리스크
- 일부 vendor TUI는 의도적으로 큰 들여쓰기를 사용하므로, compact 규칙이 너무 강하면 시각적 구조가 약간 눌려 보일 수 있습니다.
- 영문 code/log 줄은 reflow 과정에서 띄어쓰기 추정이 완벽하지 않을 수 있습니다.
- 필요하면 후속으로 lane별 normalization 강도를 다르게 두거나 “raw/compact” 이중 토글로 더 세밀하게 나눌 수 있습니다.
