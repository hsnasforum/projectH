# Pipeline GUI Guide newest-valid-control truth sync

## 변경 파일

- `pipeline_gui/guide.py` — DEFAULT_GUIDE 텍스트 갱신
- `tests/test_pipeline_gui_guide.py` — 신규 회귀 테스트

## 사용 skill

- 없음 (bounded docs-truth 수정)

## 변경 이유

`pipeline_gui/guide.py`의 DEFAULT_GUIDE가 launcher Guide 패널에 그대로 표시되는데,
stage-3 watcher 의미론(newest-valid-control dispatch, implement_blocked 자동 Codex triage 전환,
비활성 stale control 무시)이 반영되지 않아 operator에게 오래된 정보를 보여주고 있었음.

## 핵심 변경

1. **시작 시 첫 에이전트 결정** 섹션: "newest-valid-control 기준"으로 제목·본문 갱신.
   오래된 control 파일이 비활성(inactive/stale)으로 무시됨을 명시.
2. **Claude (구현)** 섹션: `implement_blocked` emit → watcher 자동 Codex triage 전환 설명 추가.
3. **control file 우선순위** 섹션: newest-valid-control 원칙과 inactive/stale 파일 무시 설명 추가.
4. **implement_blocked 자동 전환** 섹션: 자동 중단 조건 아래에 신규 섹션 추가.
5. **회귀 테스트** (`tests/test_pipeline_gui_guide.py`):
   - `newest-valid-control` 문구 존재
   - `inactive`/`stale`/`비활성` 문구 존재
   - `implement_blocked` 문구 존재
   - `Codex triage` 연결 문구 존재

## 검증

```
python3 -m unittest -v tests.test_pipeline_gui_guide  # 4/4 OK
python3 -m py_compile pipeline_gui/guide.py            # OK
git diff --check                                       # clean
```

## 남은 리스크

- Guide 텍스트만 갱신했으며 watcher 런타임 동작은 이 라운드에서 변경하지 않음.
- system-card 전체 리디자인이나 launcher 위젯 추가는 별도 슬라이스.
- `.pipeline/README.md`, `AGENTS.md` 등 기존 operator docs는 이미 truthful하므로 이번 라운드에서 수정하지 않음.
