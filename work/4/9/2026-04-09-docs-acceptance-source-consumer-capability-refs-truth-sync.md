# docs: ACCEPTANCE_CRITERIA source-consumer helper and capability_source_refs truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 1066, 1072): source-consumer 헬퍼 상태와 capability_source_refs 내부 상태 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 1066: "may materialize only"로 기술하지만, 현재 직렬화기가 이미 구체화 (`app/serializers.py:1768-1887`)
- line 1072: "future internal machinery only"로 기술하지만, 현재 직렬화기가 이미 전체 내부 소스 참조 family 해소 (`app/serializers.py:3654-3689`, `tests/test_web_app.py:2197-2239`)
- PRODUCT_SPEC(line 1411-1416)과 ARCHITECTURE(line 1111-1117)는 이미 정확하게 기술

## 핵심 변경
- "may materialize only" → "now materializes only"
- "remains future internal machinery only" → "is current internal machinery that stays payload-hidden"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 2줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — source-consumer 헬퍼 및 capability_source_refs 내부 상태 진실 동기화 완료
