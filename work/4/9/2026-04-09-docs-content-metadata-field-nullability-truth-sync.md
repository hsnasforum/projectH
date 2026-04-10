# docs: response payload content/metadata field nullability truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Content Fields 섹션(line 303-305)과 Metadata And Panel Fields 섹션(line 308-311)에서 5개 필드에 `null` 시맨틱 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `core/agent_loop.py:76-78, 90`에서 `note_preview`, `approval`, `active_context`, `applied_preferences` 모두 `None` 가능
- `app/serializers.py:49-54, 300-320`에서 nullable로 직렬화
- 셸(`app/static/app.js:3181-3183, 3212-3214, 3218-3224`)도 부재/null 폴백 경로로 소비
- `docs/ARCHITECTURE.md:151-156`은 이미 `string | null` / `object | null` / `list | null`로 정확
- `docs/PRODUCT_SPEC.md`만 항상 존재하는 것처럼 기술하여 진실 불일치 존재

## 핵심 변경
- `note_preview`: `, or null when no save is requested`
- `selected_source_paths`: `, or null`
- `approval`: `, or null when no pending approval exists`
- `active_context`: `, or null`
- `applied_preferences`: `, or null`

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 5줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 콘텐츠/메타데이터 필드 nullability 진실 동기화 완료
