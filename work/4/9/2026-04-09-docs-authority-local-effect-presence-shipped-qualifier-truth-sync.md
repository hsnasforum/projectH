# docs: PRODUCT_SPEC ARCHITECTURE ACCEPTANCE_CRITERIA local effect presence chain shipped qualifier truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 8곳(line 1339, 1350, 1367, 1383, 1415, 1487-1489, 1491): proof boundary/record, fact source, event, producer/event-source/source-consumer 체인의 "later"/"should stay"/"must later materialize" 수식어 제거
- `docs/ARCHITECTURE.md` — 4곳(line 1055-1056, 1063, 1116): 동일 체인의 "later" 수식어 제거
- `docs/ACCEPTANCE_CRITERIA.md` — 3곳(line 1030, 1041, 1063): 동일 체인의 "later" 수식어 제거

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 동일 문서 내에서 line 1304-1313(PRODUCT_SPEC), 1051-1062(ARCHITECTURE), 993-1004(ACCEPTANCE_CRITERIA)가 이미 "current implementation now evaluates/materializes"로 구체화 완료 기술
- 후속 행에서 동일 헬퍼를 "later"/"should stay"/"must later materialize"로 기술하여 모순
- NEXT_STEPS는 이전 슬라이스에서 이미 수정 완료

## 핵심 변경
- PRODUCT_SPEC: proof boundary/record/fact source/event → "now-materialized", producer/event-source/source-consumer → "materializes" (현재형), disable-side handle → "when implemented"
- ARCHITECTURE: proof boundary/record/fact source → "now-materialized", shared target → "now-materialized rollback handle (and later disable handles when implemented)"
- ACCEPTANCE_CRITERIA: fact source/event → "now-materialized", shared target → 동일 패턴

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 16줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 3개 권위 문서 + NEXT_STEPS 모두 local-effect-presence 체인 shipped 수식어 진실 동기화 완료
