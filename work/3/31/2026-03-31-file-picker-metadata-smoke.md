# 2026-03-31 browser file picker single-source metadata smoke assertion

## 목표
browser file picker 단일 문서 요약 응답에서 quick-meta와 transcript meta가 source filename(`long-summary-fixture.md`)과 `문서 요약` label을 유지한다는 현재 shipped 계약을 browser smoke로 고정.

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`: scenario 2에 quick-meta/transcript meta assertion 4줄 추가
- `README.md`: scenario 2 설명에 metadata coverage 반영
- `docs/ACCEPTANCE_CRITERIA.md`: scenario 2 설명에 metadata coverage 반영
- `docs/MILESTONES.md`: smoke suite 설명에 browser file picker metadata coverage 반영
- `docs/TASK_BACKLOG.md`: smoke coverage 설명에 browser file picker metadata coverage 반영

## 변경 내용
- scenario 2(`브라우저 파일 선택으로도 파일 요약이 됩니다`)에 4줄 추가:
  - `#response-quick-meta-text`가 `long-summary-fixture.md`를 포함하는지 assert
  - `#response-quick-meta-text`가 `문서 요약`을 포함하는지 assert
  - transcript meta `.last()`가 `long-summary-fixture.md`를 포함하는지 assert
  - transcript meta `.last()`가 `문서 요약`을 포함하는지 assert
- 기존 selector(`#response-quick-meta-text`, `data-testid="transcript-meta"`)를 그대로 재사용, selector 추가 없음.

## 검증
- `git diff --check`: whitespace 오류 없음
- `make e2e-test`: 13 passed (전체 통과)

## 리스크
- 없음. source-path summary scenario(scenario 1)와 동일한 contract를 browser file picker path에서도 고정하는 것이므로 behavior 변경 없음.

## 사용 스킬
- 없음 (직접 편집)
