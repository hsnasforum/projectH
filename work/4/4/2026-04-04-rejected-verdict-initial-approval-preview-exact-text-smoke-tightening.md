# rejected-verdict initial approval-preview exact-text smoke tightening

날짜: 2026-04-04

## 목표

rejected-verdict scenario에서 initial `#approval-preview` assertion 1건을 partial `toContainText`에서 exact-text `toHaveText(expectedNotePreview)`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 379→379-388)
  - `toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.")` → `toHaveText(expectedNotePreview)`
  - `expectedNotePreview`는 `path.basename(longFixturePath)`, `longFixturePath`, `middleSignal`, 그리고 mock의 deterministic note-body contract (`create_summary_note` format + `_summarize_chunk_outline` 결과)로 구성
  - line 389의 `originalApprovalPreview` capture와 line 409의 later immutability exact check는 그대로 유지

## 변경하지 않��� 것

- corrected-save scenario (line 462/469/470/501)
- approval-meta assertions (line 450-453)
- `#notice-box`, content-reject/reason assertions
- runtime logic (`app/static/app.js`), template (`app/templates/index.html`), docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과 (whitespace 에러 없음)
- `rg` 교차 확인: `#approval-preview` 참조가 spec/template/app.js 간 정합 확인
- `make e2e-test`: **17 passed (3.8m)**
  - 이번 슬라이스 대상 test #8 (`내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다`): **passed**
  - 모든 17건 통과

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## expected value 구성 근거

- mock의 `_summarize_chunk_outline` 결과는 fixture 파일 내용에 대해 deterministic (240 chars)
- Python simulation으로 fixture → chunking → individual chunk summarization → reduce → chunk outline → note_body → preview 전체 파이프라인 검증
- `create_summary_note` format: `# {fileName} 요약\n\n원본 파일: {sourcePath}\n\n## 요약\n{summary}`
- preview 1200자 미만이므로 truncation 없음

## 잔여 리스크

- corrected-save line 470의 negative partial check (`not.toContainText("수정본 B입니다.")`)는 line 469의 exact-text가 이미 커버하므로 후순위
- mock의 `_summarize_chunk_outline` 알고리즘이 변경되면 expected value도 함께 갱신 필요
