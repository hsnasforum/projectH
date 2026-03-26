# Task Backlog

## Done in the Current Web MVP Slice
1. 승인 객체(`approval_id`) 기반 저장 흐름 구현
2. JSON 세션 스키마와 `pending_approvals` 저장
3. JSONL 로그에 요청, 읽기, 검색, 요약, 승인 요청, 승인 실행, 실패 기록
4. 웹 UI에 최근 세션 목록, 대화 기록, 노트 미리보기, 승인 카드 추가
5. 저장 경로 allowlist와 overwrite 기본 거부 정책 반영
6. 스캔본 PDF의 OCR 미지원 안내 반영
7. 승인 카드에서 저장 경로 재입력 후 approval 재발급 지원
8. 근거 패널과 요약 구간 패널 추가
9. 스트리밍 중 취소 버튼과 진행 단계 표시 추가
10. response origin 배지와 세션 타임라인 메타 정리
11. Playwright 기반 브라우저 스모크 4개 시나리오 실행 및 안정화
12. 닫힌 고급 설정을 고려한 E2E용 `data-testid`와 독립 세션 격리 반영

## Next 5 Tasks
1. 승인/저장/실패 이력을 세션 화면에서 더 직접적으로 필터링/강조
2. 로그 분석용 간단한 로컬 뷰어 또는 요약 스크립트 추가
3. SQLite 전환 전 JSON 스키마 버전업 전략 문서화
4. 패널/카드 레이아웃을 더 압축해 데모 가독성 향상
5. Playwright 스모크를 CI 또는 상위 실행 커맨드로 통합

## Later
1. SQLite 저장소 도입
2. 웹 UI를 컴포넌트 구조로 재편
3. OCR 도입 여부 재검토
4. 모델 평가 기준과 실패 패턴 수집 체계 추가
5. 교체 가능한 독자 모델 런타임 인터페이스 고도화
