# docs: ACCEPTANCE_CRITERIA proof-boundary and proof-record materialized wording truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 997, 998): proof boundary "now stays" → "is one now-materialized", proof record "must stay" → "is one now-materialized"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- PRODUCT_SPEC(line 1339-1350)과 ARCHITECTURE(line 1055-1056)는 이미 "now-materialized"로 정확하게 기술
- `app/serializers.py:1904-2008, 2010-2130`에서 proof boundary와 proof record를 현재 내부 저장소 경로에서 구체화
- `tests/test_smoke.py:5913-6054`에서 구체화 경로 잠금
- ACCEPTANCE_CRITERIA만 "now stays"/"must stay"로 약하게 기술

## 핵심 변경
- proof boundary: "now stays one shared internal" → "is one now-materialized shared internal"
- proof record: "must stay one internal" → "is one now-materialized internal"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 2줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — proof boundary/record 구체화 문구 진실 동기화 완료
