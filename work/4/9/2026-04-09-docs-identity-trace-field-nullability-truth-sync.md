# docs: response payload identity trace field nullability truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — `### Identity And Trace Fields` 섹션(line 297-300)에서 3개 필드에 `null` 시맨틱 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `core/agent_loop.py:69, 86-87`에서 `artifact_id`, `artifact_kind`, `source_message_id` 모두 `None` 가능
- `app/serializers.py:36-40, 390-394`에서 nullable로 직렬화
- 에러/시스템 경로(`core/agent_loop.py:391-395, 399-403, 8775-8794`)에서 해당 앵커 없이 반환
- `docs/ARCHITECTURE.md:147-149`는 이미 `string | null`로 정확하게 기술
- `docs/PRODUCT_SPEC.md`만 항상 존재하는 것처럼 기술하여 진실 불일치 존재

## 핵심 변경
- 섹션 제목에 `(null when no grounded-brief artifact exists)` 추가
- 3개 필드 각각에 `, or null` 명시

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 4줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 아이덴티티/트레이스 필드 nullability 진실 동기화 완료
