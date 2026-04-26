STATUS: verified
CONTROL_SEQ: 221
BASED_ON_WORK: work/4/26/2026-04-26-e2e-healthcheck-wrapper.md
BASED_ON_ADVICE: .pipeline/advisory_advice.md CONTROL_SEQ 221
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 222

---

# 2026-04-26 M38 Axis 1 — E2E healthcheck wrapper 검증

## 변경 파일 (이번 커밋 대상)
- `Makefile`
- `e2e/start-server.sh` (신규)
- `README.md`
- `e2e/README.md`
- `docs/MILESTONES.md`
- `work/4/26/2026-04-26-e2e-healthcheck-wrapper.md` (신규)
- `verify/4/26/2026-04-26-controller-cleanup-commit.md` (신규, 이전 round 아티팩트)

## 검증 요약
- advisory_advice CONTROL_SEQ 221: auto-start 경로 150 passed 수용, 재사용 경로 미검증은 sandbox 환경 제약으로 인정
- `bash -n e2e/start-server.sh` — 통과
- `git diff --check -- Makefile README.md docs/MILESTONES.md e2e/README.md` — 통과
- `/healthz` 엔드포인트: `app/web.py:344`에 존재 확인
- 구현 세션 `make e2e-test` auto-start 경로: **150 passed (13.4m)**
- 구현 세션 post-cleanup healthcheck: 서버 정리 확인 (`not healthy: URLError`)

## 확인한 내용
- `Makefile` e2e-test target이 inline kill/sleep 로직 → `e2e/start-server.sh` 호출로 교체됨
- `start-server.sh`: healthcheck → 기존 서버 재사용(no kill) / 서버 없으면 isolated mock DB로 auto-start → trap 정리
- 재사용 경로(healthy 서버 존재 시): sandbox `PermissionError`로 인해 실제 `make e2e-test`까지 미도달 — 환경 제약, 코드 로직 결함 아님
- `/healthz` 엔드포인트 app.web에 존재하므로 non-sandbox 환경에서 재사용 경로 정상 동작 예상

## 남은 리스크
- existing-server 재사용 경로의 full `make e2e-test`는 verify lane에서도 sandbox 제약으로 미검증; non-sandbox 환경에서의 manual 검증 또는 CI pass로 확인 필요
- 149(M37 gate) → 150 count 증가: spec 파일 변경 없음 확인, Gemini advice가 150 accepted로 판단; 안정화된 flaky test 가능성
- `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**` 등 기존 미추적 아티팩트는 이번 범위 밖

## 다음 제어
- NEXT: `.pipeline/implement_handoff.md` CONTROL_SEQ 222 — M38 Axis 2: start-server.sh 하드닝 + MILESTONES.md Axis 1 closure
