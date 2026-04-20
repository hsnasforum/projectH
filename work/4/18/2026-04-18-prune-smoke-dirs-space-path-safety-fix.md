# 2026-04-18 `_smoke_enumerate_dirs` 공백 포함 경로 truncation 버그 수정

## 변경 파일
- `.pipeline/smoke-cleanup-lib.sh`
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-prune-smoke-dirs-protect-tracked-dry-run-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 shared helper `prune_smoke_dirs`의 protected 경로 dry-run 계약을 direct-caller regression으로 잠갔습니다.
- 같은 smoke-cleanup owner 경계에서 이번 라운드는 regression 추가가 아니라 실제 bug 수정입니다. `_smoke_enumerate_dirs`가 `find -printf '%T@ %p\n' | sort -nr | awk '{print $2}'`로 path를 추출하고 있어, smoke 디렉터리 이름에 공백이 들어가면 `awk '{print $2}'`가 첫 공백 앞까지만 읽고 그 뒤 segment는 버렸습니다. 그 결과:
  - stdout은 `KEEP /tmp/.../live-arb-smoke` / `DELETE /tmp/.../live-arb-smoke`처럼 잘린 경로를 찍고
  - 실제 `live-arb-smoke newest` / `live-arb-smoke older` 디렉터리는 truncated path로는 `rm -rf`가 매칭하지 못해 디스크에 그대로 남는
  - silent correctness bug가 존재했습니다.
- 이번 slice는 그 버그를 helper 한 곳에서 고치고, 공백 포함 디렉터리 이름에 대해 live/dry-run 두 경로가 full-path diagnostic + 올바른 디렉터리 결과를 유지하도록 direct-caller regression을 같이 추가합니다. scope는 `.pipeline/smoke-cleanup-lib.sh` + `.pipeline/README.md` + `tests/test_pipeline_smoke_cleanup.py` 안으로 제한합니다.

## 핵심 변경
- `.pipeline/smoke-cleanup-lib.sh`의 `_smoke_enumerate_dirs`를 수정해, `find -printf '%T@\t%p\n'`(탭 구분자) + `sort -nr` + `cut -f2-` 조합으로 변경했습니다. 이제 mtime과 path는 탭 한 문자로만 구분되며, path에 공백이 몇 개 들어와도 `cut -f2-`가 첫 탭 뒤 전체를 그대로 반환해 downstream `mapfile -t dirs < <(...)`가 한 줄 = 한 full path로 받게 됩니다.
  - 기존 공백 없는 이름에 대한 동작은 그대로입니다. `find -printf` 포맷이 공백 → 탭으로만 바뀌었고, `sort -nr`는 선행 숫자 필드 기준 정렬이 동일하며, `cut -f2-`는 탭 뒤 전체를 유지하므로 경로에 공백이 있든 없든 동일한 newest-first 순서를 돌려줍니다.
  - 헬퍼 주석에 "탭/개행 문자 포함 path는 여전히 지원하지 않는다"는 downstream `mapfile -t` 한계도 남겼습니다. 현재 실제 smoke 디렉터리 이름에는 탭/개행이 들어오지 않으므로 이 단계에서 null-byte separator까지 가지 않고 탭만으로 공백 문제를 닫았습니다.
- `tests/test_pipeline_smoke_cleanup.py`에 `test_prune_smoke_dirs_preserves_paths_with_spaces`를 추가했습니다. 임시 repo에 `live-arb-smoke older`(mtime 100), `live-arb-smoke newest`(mtime 300) 두 디렉터리를 둔 뒤 아래 두 케이스를 같은 테스트에서 잇달아 돕니다.
  1. `_call_prune(root, "live-arb-smoke*", keep_recent=1, protect_tracked=0, dry_run=1)` → stdout에 `KEEP <newest full path>`, `DELETE <older full path>`가 공백까지 그대로 보이는지, 두 디렉터리가 dry-run 뒤에도 모두 남는지 확인합니다. dry-run이 실제 삭제를 일으키지 않는다는 기존 계약을 공백 경로에서도 같이 잠급니다.
  2. 이어서 `dry_run=0`으로 같은 helper를 호출해 stdout 진단은 같은 full-path 형식이면서 `older` 디렉터리는 실제로 삭제되고 `newest`는 보존되는지 확인합니다. "truncation이 없다면 실제 삭제도 되어야 한다"는 포인트를 assertion 메시지로 남겼습니다.
- `.pipeline/cleanup-old-smoke-dirs.sh`와 wrapper helper(`prune_blocked_smoke_dirs`, `prune_live_arb_smoke_dirs`, `prune_manual_smoke_dirs`)는 이번 라운드에서 수정하지 않았습니다. 모두 `_smoke_enumerate_dirs`를 통해 `prune_smoke_dirs`로 내려가므로 이번 fix가 자동으로 전체 경로에 반영됩니다. 기존 no-space 회귀는 그대로 통과합니다.
- `.pipeline/README.md`는 이번 라운드에서 수정하지 않았습니다. 기존 `smoke 디렉터리 정리 규약` 섹션의 `KEEP/PROTECT/DELETE <path>` 표기는 그대로 참이며, "공백 포함 이름을 명시적으로 지원한다"를 새로 문서화하는 것은 문구 추가성 docs 변경이라 handoff scope-limits의 "docs-only dedupe 금지" 쪽으로 흐를 여지가 있어 피했습니다. 현재 READme 설명과 이번 code 변경 사이에 drift는 발생하지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 27 tests`, `OK`. 신규 `test_prune_smoke_dirs_preserves_paths_with_spaces` 한 건이 현재 tree에서 실제로 녹색이며, 기존 26건(manual/live-arb/blocked wrapper, script receipts, helper guards, live-arb direct stdout, protected dry-run 등)은 fix 이후에도 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 handoff가 요구한 direct-helper rerun을 두 번 실행했습니다.
  - dry-run: `prune_smoke_dirs "<tmpdir>/.pipeline" "live-arb-smoke*" 1 0 1` → stdout `KEEP <tmpdir>/.pipeline/live-arb-smoke newest`, `DELETE <tmpdir>/.pipeline/live-arb-smoke older`가 전체 경로로 찍히고 두 디렉터리 모두 디스크에 남았습니다.
  - live: 같은 helper를 `dry_run=0`으로 호출 → stdout은 동일한 full-path 진단, `older` 디렉터리는 실제 삭제, `newest`는 보존됐습니다.
  두 rerun은 bug 전의 `awk '{print $2}'` 동작("KEEP /.../live-arb-smoke" 같은 truncated path + 실제 삭제 누락)과 명확히 다른 결과를 보여 주며, 이번 fix가 문제를 실제로 닫았음을 직접 확인합니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 shared helper enumeration 단계의 path-safety만 좁게 고쳤고 tmux dispatch / runtime state writer / shipped browser contract를 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `.pipeline/smoke-cleanup-lib.sh`와 `tests/test_pipeline_smoke_cleanup.py` 두 개이고, `.pipeline/cleanup-old-smoke-dirs.sh`와 `.pipeline/README.md`는 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- Helper는 여전히 path에 탭이나 개행이 들어오면 `mapfile -t` 경계에서 깨집니다. 실제 smoke 디렉터리 이름은 tooling이 `mktemp -d` 등으로 생성하므로 탭/개행은 현실적으로 들어오지 않지만, 외부 조작된 이름에 대해 완전히 path-safe하려면 find `-print0` + `sort -z` + `cut -z` + `mapfile -d ''` 전면 개편이 필요합니다. 이번 slice는 handoff가 요구한 공백 안전성만 좁게 닫았고, 탭/개행 단계 방어는 scope 밖으로 남겼습니다.
- 새 테스트는 stdout substring 기반으로 `KEEP <full path>` / `DELETE <full path>`를 잠급니다. 진단 포맷을 바꾸고 싶다면 이 테스트와 기존 live-arb/blocked/manual direct-caller regressions를 한 라운드에서 같이 움직여야 drift 없이 넘어갈 수 있습니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, README 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 중복 정리, helper stdout 포맷 규약 문서화 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 `_smoke_enumerate_dirs` newline/null-byte path-safety 확장, wrapper 경계에서 특수문자 path 다루는 end-to-end manual cleanup script regression, 또는 README 두 섹션 중복 정리가 남아 있습니다.
