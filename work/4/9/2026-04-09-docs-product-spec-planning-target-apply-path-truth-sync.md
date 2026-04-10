# docs: PRODUCT_SPEC planning-target marker apply-path truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 1곳(line 1202): planning-target 마커 블록에서 apply-path 부정 제거, shipped 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 1202가 "no reviewed-memory apply path"로 전역 부정
- 동일 문서에서 이미 출하된 apply 라이프사이클 기술 (line 1537-1540)
- line 1178-1184에서 planning-target/unblock 의미가 apply보다 좁다고 기술
- ARCHITECTURE(line 907-913)과 ACCEPTANCE_CRITERIA(line 806)는 이미 로컬 가드레일 프레이밍 사용

## 핵심 변경
- "no reviewed-memory apply path" → "the reviewed-memory apply path is now shipped above this planning-target marker layer"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — planning-target 마커의 apply-path 부정 진실 동기화 완료
