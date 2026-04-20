# 2026-04-19 investigation claim conflict status separation verification

## 변경 파일
- `verify/4/19/2026-04-19-investigation-claim-conflict-status-separation-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-investigation-claim-conflict-status-separation.md`)를 현재 tree와 대조해 truth를 재확인하고, 같은 날 다른 family용 verify 노트를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 366이 Gemini advice 365 기반으로 `Investigation Claim Conflict Status Separation` slice를 implement로 닫았고, Codex가 `/work`로 closeout했지만 같은 날 verify 폴더에는 이 family에 매칭되는 verify 노트가 아직 없었습니다.
- 같은 날 직전 verify(`verify/4/19/2026-04-19-watcher-role-bound-turn-state-surface-verification.md`)는 watcher role-bound turn-state family라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.
- seq 365 advice가 좁힌 slot coverage CONFLICT 계약이 현재 tree에 truthful하게 들어왔는지, 그리고 `/work`가 명시한 downstream untouched 영역이 실제로 그대로인지 고정해야 다음 control 선택이 안전합니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/contracts.py:123-127`에 `CoverageStatus`가 `STRONG`/`CONFLICT`/`WEAK`/`MISSING` 4개 값으로 확장되어 있고, `CONFLICT = "conflict"`가 실제로 string-enum 스타일을 유지한 채 추가되어 있습니다.
  - `core/web_claims.py:166-196`의 `summarize_slot_coverage()`가 `has_trusted_agreement and not has_conflict`일 때만 `STRONG`을 반환하고, `has_conflict`가 참이면 `CONFLICT`, 그 외 path는 기존처럼 `WEAK`로 떨어뜨립니다. `_has_competing_trusted_alternative` 헬퍼 자체는 손대지 않았습니다.
  - `tests/test_smoke.py:2053-2148`에서 untrusted-only `WEAK`, conflicting trusted alternative `CONFLICT`, non-conflict `STRONG`, 빈 슬롯 `MISSING` 4개 표면이 한 묶음으로 고정되어 있습니다.
- focused rerun은 모두 통과했습니다.
  - `python3 -m unittest tests.test_smoke -k summarize_slot_coverage` → `Ran 2 tests`, `OK`
  - `python3 -m py_compile core/contracts.py core/web_claims.py tests/test_smoke.py` → 출력 없음, exit `0`
  - `git diff --check -- core/contracts.py core/web_claims.py tests/test_smoke.py` → 출력 없음, exit `0`
- 보수적으로 broader enum membership을 한 번 더 확인하기 위해 `python3 -m unittest tests.test_contracts` → `Ran 45 tests`, `OK`. 기존 `STRONG`/`WEAK`/`MISSING` 값 동등성 assertion은 그대로이고, 새 `CONFLICT` 값은 enum 전체 집합을 락하지 않은 덕분에 회귀 없이 추가됐습니다.
- `/work`가 명시한 downstream untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `app/serializers.py:283-285`는 여전히 `STRONG`/`WEAK`/`MISSING` 3개 값만 `claim_coverage_summary`에 합산합니다. CONFLICT 슬롯은 새 카운터로 분리되지 않습니다.
  - `core/agent_loop.py`의 `_claim_coverage_status_rank`(4317-4324), `_claim_coverage_status_label`(4325-4332), `current_status in {CoverageStatus.WEAK, CoverageStatus.MISSING}`(4411), `if status == CoverageStatus.WEAK and compact_value`(3729) 같은 분기는 모두 4값 enum 확장 이전 형태로 남아 있어 CONFLICT는 라벨/랭크/unresolved 집합에서 fall-through 처리됩니다.
  - 즉 이번 라운드는 contract 레벨에서 CONFLICT를 표면화한 단계까지만 truthful하게 진행됐고, downstream payload/UI 노출은 의도적으로 다음 라운드 몫으로 남았습니다.

## 검증
- 직접 코드/테스트 대조
  - 대상: `core/contracts.py`, `core/web_claims.py`, `tests/test_smoke.py`, `tests/test_contracts.py`, `app/serializers.py`, `core/agent_loop.py`.
  - 결과: `/work`가 설명한 `CoverageStatus.CONFLICT` 추가, `summarize_slot_coverage()` 분기, focused regression 추가가 현재 tree와 일치하고, downstream untouched 영역도 `/work`의 `남은 리스크` 기재와 일치함을 확인했습니다.
- `python3 -m unittest tests.test_smoke -k summarize_slot_coverage`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest tests.test_contracts`
  - 결과: `Ran 45 tests`, `OK` (broader enum 회귀 없음)
- `python3 -m py_compile core/contracts.py core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`
- `git diff --check -- core/contracts.py core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`
- broader `tests.test_smoke` 전체, `tests.test_web_app`, Playwright, `make e2e-test`은 이번 verify에서 다시 돌리지 않았습니다.
  - 이유: 이번 `/work`는 browser-visible 계약이나 공유 브라우저 helper를 바꾸지 않았고, 슬롯 커버리지 계약 자체에 좁게 한정된 enum 확장입니다. focused regression 2건 + 보수적 broader 컨트랙트 enum 회귀 1건이 현재 truth 판정에 충분했습니다.

## 남은 리스크
- `app/serializers.py`의 `claim_coverage_summary`는 여전히 `STRONG`/`WEAK`/`MISSING` 3개 키만 합산합니다. CONFLICT 슬롯은 별도 카운트가 아니라서 외부 client는 "trusted 충돌"과 "근거 부족"을 같은 카운터로 보지 못합니다. 다음 라운드 후보입니다.
- `core/agent_loop.py`의 `_claim_coverage_status_label`/`_claim_coverage_status_rank`/unresolved 집합/`compact_value` weak 분기는 CONFLICT를 별도 라벨/랭크/unresolved 의미로 다루지 않습니다. 이대로면 CONFLICT 슬롯이 UI/내부 로직에서 비-STRONG fallback인 "단일 출처" 라벨로 보일 수 있어, 슬롯 reinvestigation/entity-card 정책에서 신호가 평탄화될 수 있습니다. 이것도 같은 family의 자연스러운 다음 라운드입니다.
- seq 363 `.pipeline/operator_request.md`가 던진 `Milestone 4 exact slice` 질문은 이번 슬라이스(seq 365 advice → seq 366 implement)로 부분적으로만 답해졌습니다. CONFLICT 표면화는 한 발 진전이지만, `source role labeling/weighting`, `strong vs weak vs unresolved separation`의 broader 두 축은 아직 exact slice가 정해지지 않았습니다.
- broad `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` failure는 이번 라운드 범위 밖이고 별도 truth-sync 라운드 몫으로 dirty state에 남아 있습니다.
