# Next Steps

## Current Checkpoint
- Python 기반 로컬 웹 셸이 `127.0.0.1`에서 동작합니다.
- 파일 요약, 문서 검색, 세션 저장, JSONL 로그 기록이 연결되어 있습니다.
- 저장은 즉시 실행되지 않고 `approval_id`를 가진 승인 객체를 거쳐야 합니다.
- 승인 카드에서 저장 경로를 수정하면 기존 approval을 바로 실행하지 않고 새 approval로 다시 발급합니다.
- 세션 JSON에는 `schema_version`, `title`, `messages`, `pending_approvals`, `created_at`, `updated_at`가 남습니다.
- 기본 모델 전략은 `mock` 기본값 + 선택형 `ollama`입니다.
- 최근 결과 영역에는 근거 패널, 요약 구간 패널, response origin 배지, 스트리밍 취소가 반영되어 있습니다.
- WSL 환경에서 Playwright 브라우저 스모크 4개 시나리오를 실제 실행해 통과했습니다.

## Immediate Implementation Order
1. 응답/근거/요약 구간 패널의 UI를 더 간결한 카드형 레이아웃으로 정리합니다.
2. 승인/저장/실패 로그를 UI에서 더 직접 확인할 수 있는 로컬 뷰를 추가합니다.
3. JSON 세션/로그 구조를 기준으로 SQLite migration 계획을 문서화합니다.
4. PDF 텍스트 레이어 지원 범위와 OCR 미지원 안내를 사용자 문서에 더 분명히 정리합니다.
5. Playwright 스모크를 CI 또는 상위 실행 스크립트에 연결합니다.

## Current Constraint
- 브라우저 스모크는 현재 `mock` 프로바이더 기준으로 안정화되어 있으며, `ollama` 품질/속도는 수동 확인 체크리스트로 유지합니다.

## Explicitly Deferred
- Next.js 전환
- SQLite 전환
- OCR 도입
- 독자 모델 개발
- 덮어쓰기 승인 허용
