# docs: approval_reason_record reject-reissue truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 승인 객체 섹션(line 200)과 응답 페이로드 보정 필드 섹션(line 320)에서 `reissued approvals` → `rejected or reissued approvals`
- `docs/ARCHITECTURE.md` — 응답 페이로드 테이블(line 163)에서 `reissue reason record` → `reject or reissue reason record`, 승인 계약 섹션(line 290)에서 동일 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 현재 구현(`core/agent_loop.py:7229-7283` reissue 경로, `core/agent_loop.py:7303-7333` reject 경로)은 승인 거절과 재발행 모두에서 `approval_reason_record`를 노출
- 테스트도 양쪽 경로를 잠금: reissue(`tests/test_web_app.py:6391-6396`), reject(`tests/test_web_app.py:7112-7117`, `tests/test_smoke.py:2988-2994`)
- 문서는 reissue만 언급하여 reject 경로가 누락된 진실 불일치 존재

## 핵심 변경
- 4개 위치에서 "reissued approvals" 또는 "reissue reason record"를 "rejected or reissued approvals" / "reject or reissue reason record"로 수정
- ACCEPTANCE_CRITERIA는 이미 `approval_reject`와 `approval_reissue` 양쪽을 정확히 기술하므로 변경 불필요

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md` — 2개 파일, 4줄 변경 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — `approval_reason_record`의 reject/reissue 범위 진실 동기화 완료
