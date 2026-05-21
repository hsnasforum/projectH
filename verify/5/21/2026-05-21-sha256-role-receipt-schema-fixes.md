# verify: 2026-05-21 sha256/role-owners/receipt schema fixes (B7/B10/C8)

## 대상 work
`work/5/21/2026-05-21-sha256-role-receipt-schema-fixes.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` schema / state_contract / receipts | PASS |
| `unittest` supervisor(215) + schema + state_contract = 276개 | PASS (1.569s) |
| `git diff --check` | PASS |

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| B7: `sha256_file()` → `iter(lambda: f.read(65536), b"")` 청크 읽기 | schema.py:342–346 | ✓ |
| C8: `RECEIPT_SCHEMA_VERSION = "1"` 상수 + `build_receipt()` 참조 | receipts.py:8, 89 | ✓ |
| B10: `_role_owners()` → `default_role_bindings()` import 통일 | state_contract.py:7, 285 | ✓ |

## 중요 보정

지시사항의 `advisory: ""` 기본값 가정은 틀렸습니다.
실제 `lane_catalog._DEFAULT_ROLE_BINDINGS`의 `advisory: "Claude"`가 맞고,
Codex가 이 현재 source of truth를 따라 수정했습니다. 올바른 판단입니다.

## 다음 슬라이스

**핸드오프 3** — state_contract 분해(B9) + events.jsonl 로테이션(D2)
