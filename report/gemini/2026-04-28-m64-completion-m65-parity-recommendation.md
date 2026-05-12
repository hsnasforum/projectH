# Advisory Log: 2026-04-28 — M64 완료 및 M65 SQLite Parity 권고

## 개요
M64 Axis 1+2 완료를 통해 "교정 패턴 승인" 기능이 추가되었으나, 현재 이 기능은 JSON 기반 `CorrectionStore`에만 구현되어 있음. 프로젝트의 기본 저장소인 `SQLiteCorrectionStore`에는 관련 메서드가 누락되어 있어, 기본 설정(Default Configuration)에서 런타임 에러가 발생할 위험이 큼.

## 분석
- **현 상태**: M61-M64를 통해 추가된 `_scan_all()`, `confirm_by_fingerprint()` 등의 메서드가 `SQLiteCorrectionStore`에는 구현되지 않음.
- **리스크**: `DEFAULT_STORAGE_BACKEND = "sqlite"`인 상황에서 `/api/corrections/summary` 호출 시 `_scan_all` 누락으로 인한 크래시, 승인 버튼 클릭 시 `confirm_by_fingerprint` 누락으로 인한 크래시가 발생함.
- **기술적 부채**: TypedDict 시리즈(M54-M60)를 통해 확보한 SQLite-JSON 패리티가 최신 기능에서 다시 깨진 상태임.

## 권고 사항
`RECOMMEND: implement M65 Axis 1 — SQLite CorrectionStore Parity`

### 권고 이유
1. **Technical Integrity**: 기본 저장소에서 최신 기능이 작동하지 않는 것은 심각한 결함임.
2. **Same-family current-risk reduction**: 런타임 크래시 리스크를 제거하고 시스템 안정성을 확보해야 함.
3. **Foundation for Next Steps**: "Dismiss" 등 추가 기능을 구현하기 전에 기존 기능의 스토리지 패리티를 맞추는 것이 선행되어야 함.

### 구현 슬라이스
- `storage/sqlite_store.py`: `SQLiteCorrectionStore`에 `_scan_all()`, `confirm_by_fingerprint()` 메서드 추가.
- `tests/test_sqlite_store.py` (또는 관련 테스트): SQLite 환경에서 교정 요약 및 패턴 승인이 정상 작동하는지 검증.

## 결론
새로운 기능을 추가하기 전에, 이미 구현된 기능이 기본 환경에서 정상 작동하도록 "스토리지 패리티"를 맞추는 M65 Axis 1 진행을 강력히 권고함.
