# docs: response payload control path field nullability truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Control Fields 섹션(line 291-293)에서 3개 경로 필드에 `null` 시맨틱 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `core/agent_loop.py:73-74, 85`에서 `proposed_note_path`, `saved_note_path`, `web_search_record_path` 모두 기본값 `None`
- `app/serializers.py:45-47`에서 직접 직렬화 (null 그대로 전달)
- 셸(`app/static/app.js:1070-1075, 1693-1703`)도 nullable/폴백 경로로 소비
- `docs/ARCHITECTURE.md:142-144`는 이미 `string | null`로 정확
- `docs/PRODUCT_SPEC.md`만 항상 존재하는 것처럼 기술

## 핵심 변경
- `proposed_note_path`: `, or null when no save is requested`
- `saved_note_path`: `, or null`
- `web_search_record_path`: `, or null when no web investigation record exists`

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 제어 경로 필드 nullability 진실 동기화 완료
