# docs: recurrence aggregate late-stage action summary truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 60, 230): aggregate 요약에 적용 중단/되돌리기/충돌 확인 추가
- `docs/ARCHITECTURE.md` — 2곳(line 80, 1329): 동일 추가
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 1358): 동일 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 5개 루트 요약이 모두 `effect_active` / `[검토 메모 활성]`에서 끝나 후속 출하 단계 누락
- 실제 출하 동작:
  - `적용 중단` → `record_stage = stopped`, 효과 제거
  - `적용 되돌리기` → `record_stage = reversed`
  - `충돌 확인` → `reviewed_memory_conflict_visibility_record`, `record_stage = conflict_visibility_checked`
- `docs/PRODUCT_SPEC.md:1531-1537`과 `e2e/tests/web-smoke.spec.mjs:900-966`에서 이미 출하 확인

## 핵심 변경
- 5개 요약 행에 stop-apply / reversal / conflict-visibility 3단계 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 5줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — aggregate 루트 요약이 전체 출하 라이프사이클 반영 완료
