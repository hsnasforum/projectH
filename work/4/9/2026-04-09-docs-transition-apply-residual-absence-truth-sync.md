# docs: PRODUCT_SPEC ARCHITECTURE reviewed-memory transition/apply residual absence truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 2곳(line 1132, 1168-1170): 출하된 transition/apply 표면을 부정하는 부재 항목 제거/수정
- `docs/PRODUCT_SPEC.md` — 1곳(line 1540-1542): "no reviewed-memory apply result" 제거, shipped 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- ARCHITECTURE: "no reviewed-memory apply path", "no current emitted reviewed-memory transition record surface", "no reviewed-memory apply" — 모두 이미 출하됨
- PRODUCT_SPEC: "no reviewed-memory apply result" — 이미 출하됨
- `app/web.py:302-306`에서 5개 aggregate transition API 노출
- `app/handlers/aggregate.py:392-415, 467-532`에서 apply_result/stop/reverse 구체화
- 동일 문서 내 다른 섹션에서 이미 shipped로 기술하여 자기 모순

## 핵심 변경
- ARCHITECTURE line 1132: "no reviewed-memory apply path" → "reviewed-memory apply path is now shipped"
- ARCHITECTURE line 1168-1170: "no emitted transition record"/"no reviewed-memory apply" → "emitted reviewed-memory transition record surface is now shipped" (2행 → 1행)
- PRODUCT_SPEC line 1540-1542: "no widening"/"no reviewed-memory apply result" → "reviewed-memory apply result is now shipped; boundary draft stays read-only" (2행 → 1행)
- 진정으로 부재한 항목(no candidate store, no proof-record surface, no repeated-signal promotion, no cross-session counting)은 그대로 유지

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 3줄 추가 / 5줄 제거 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — transition/apply 부재 항목 자기 모순 진실 동기화 완료
