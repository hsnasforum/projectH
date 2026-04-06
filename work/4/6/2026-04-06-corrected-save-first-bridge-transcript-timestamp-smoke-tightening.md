# corrected-save first bridge transcript timestamp smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+2 lines)

## 사용 skill
- 없음 (단일 파일 2줄 추가)

## 변경 이유
- `corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다` scenario는 per-message timestamp contract를 아직 smoke에서 잠그지 않은 첫 later browser flow였음
- `README.md:27,93`, `docs/ACCEPTANCE_CRITERIA.md:15`, `docs/MILESTONES.md:36`이 이미 약속한 conversation timeline per-message timestamp를 E2E에서도 보호해야 함

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs` corrected-save first bridge scenario 끝에 transcript `.message-when` first/last regex assertion 2개 추가
- assertion shape: `/오[전후]\s\d{1,2}:\d{2}/` (earlier scenarios와 동일)

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright tightening, Python 코드 변경 없음)

## 남은 리스크
- corrected-save late reject / re-correct scenario, candidate confirmation scenario, aggregate scenario는 아직 transcript timestamp assertion 미보호
- 이번 라운드에서 의도적으로 first unprotected flow 1건만 닫음
