# pipeline 시작 / handoff 점검 체크리스트

## 목적
- `설정: 준비됨` 또는 `적용 완료`처럼 보여도 실제 runtime truth가 맞는지 확인합니다.
- `Active profile is missing.`
- tmux 15초 감지 실패
- GUI/`/controller`/direct CLI의 상태 불일치
- Claude가 구현 후 멈추고 Codex verify로 자연스럽게 안 넘어가는 상황

## 1. 현재 repo가 맞는지 먼저 확인
```bash
pwd
readlink -f .
```

- 기대값: 실제 실행 대상이 `/home/xpdlqj/code/projectH`
- 다르면: GUI recent project, 터미널 cwd, controller가 보는 project root를 먼저 맞춥니다.

## 2. canonical active profile이 실제로 있는지 확인
```bash
ls -l .pipeline/config/agent_profile.json
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('.pipeline/config/agent_profile.json')
print("exists =", p.exists(), "path =", p)
if p.exists():
    print(json.dumps(json.loads(p.read_text(encoding='utf-8')), indent=2, ensure_ascii=False))
PY
```

- 없으면: runtime의 `Active profile is missing.` 차단은 정상입니다.
- 있으면: 다음 단계로 넘어갑니다.

## 3. setup canonical 파일이 실제로 남았는지 확인
```bash
ls -l .pipeline/setup
for f in .pipeline/setup/request.json .pipeline/setup/preview.json .pipeline/setup/apply.json .pipeline/setup/result.json .pipeline/setup/last_applied.json; do
  [ -f "$f" ] && { echo "=== $f ==="; sed -n '1,120p' "$f"; }
done
```

- `agent_profile.json`은 없는데 `last_applied.json`만 있으면:
  - UI가 old/stale 상태를 보여주고 있을 가능성이 큽니다.
  - apply promotion이 실제 canonical active write까지 못 간 경우일 수 있습니다.

## 4. direct CLI truth를 먼저 본다
```bash
bash -l start-pipeline.sh . --mode experimental --no-attach --session aip-projectH
```

- 여기서 막히는 메시지가 runtime truth의 1차 기준입니다.
- GUI나 `/controller`보다 direct CLI를 먼저 믿습니다.

## 5. controller stale process를 확인한다
```bash
ss -ltnp | grep 8780 || true
ps -ef | grep 'controller.server' | grep -v grep || true
```

- `Address already in use`가 나오면 기존 controller가 이미 떠 있는 것입니다.
- `/controller` 결과가 이상하면 stale controller부터 의심합니다.

## 6. GUI/EXE가 stale인지 확인한다
Windows PowerShell:

```powershell
Get-Item "$HOME\Desktop\pipeline-gui.exe" | Select-Object FullName,Length,LastWriteTime
Get-Item "\\wsl.localhost\Ubuntu\home\xpdlqj\code\projectH\dist\pipeline-gui.exe" | Select-Object FullName,Length,LastWriteTime
Get-FileHash "$HOME\Desktop\pipeline-gui.exe" -Algorithm SHA256
Get-FileHash "\\wsl.localhost\Ubuntu\home\xpdlqj\code\projectH\dist\pipeline-gui.exe" -Algorithm SHA256
```

- 길이/수정시각/SHA256이 다르면 Desktop exe가 stale입니다.
- 교체 후에는 기존 GUI 창을 모두 종료하고 다시 실행합니다.

## 7. EXE 빌드가 최신 소스를 실제로 반영했는지 확인
Windows PowerShell:

```powershell
Get-Item "\\wsl.localhost\Ubuntu\home\xpdlqj\code\projectH\dist\pipeline-gui.exe" | Select-Object FullName,Length,LastWriteTime
Get-Item "$HOME\Desktop\pipeline-gui.exe" | Select-Object FullName,Length,LastWriteTime
Get-FileHash "\\wsl.localhost\Ubuntu\home\xpdlqj\code\projectH\dist\pipeline-gui.exe" -Algorithm SHA256
Get-FileHash "$HOME\Desktop\pipeline-gui.exe" -Algorithm SHA256
```

```bash
ls -l .pipeline/gui-runtime/_data/start-pipeline.sh .pipeline/gui-runtime/_data/watcher_core.py 2>/dev/null
```

- `dist/pipeline-gui.exe`와 실제 실행한 exe의 길이/수정시각/SHA256이 다르면, 최신 소스가 실행 중이 아닙니다.
- EXE를 교체했더라도 예전 GUI 프로세스가 살아 있으면 메모리에는 이전 빌드가 계속 남습니다.
- EXE는 project 아래 `.pipeline/gui-runtime/_data/`에 staged runtime copy를 만들어 쓸 수 있으므로, `watcher_core.py`, `start-pipeline.sh`가 오래된 상태인지도 같이 확인합니다.
- PowerShell 빌드는 UNC에서 직접 `pyinstaller ...`를 치기보다 아래처럼 safe-copy 스크립트로 `%TEMP%` 로컬 staging 후 빌드하는 편이 안전합니다.
- 최신 `build-gui-exe.ps1`는 build가 끝나면 Desktop의 `pipeline-gui.exe`도 자동으로 덮어씁니다. 그래도 기존 GUI 프로세스는 자동 교체되지 않으니, 실행 중인 창은 모두 종료 후 다시 여셔야 합니다.
- 중요:
  - `python3 pipeline-gui.py`는 정상인데 EXE만 이상하면, `.pipeline/config`나 `.pipeline/setup`을 먼저 지우지 않습니다.
  - 그 경우는 설정 파일 문제가 아니라 frozen EXE snapshot 또는 staged runtime drift일 가능성이 더 큽니다.
  - 먼저 EXE를 다시 빌드하고, 실제 실행 EXE hash와 `dist/pipeline-gui.exe` hash가 같은지 확인합니다.
  - 같은 Desktop exe라도 더블클릭과 repo root PowerShell `& "$HOME\\Desktop\\pipeline-gui.exe"`가 다르게 보이면 launch cwd가 bundled import를 가로채는지 의심합니다. 최신 entrypoint는 이 shadowing을 막고 startup cwd도 exe 폴더로 정규화해야 정상입니다.

```powershell
cd \\wsl.localhost\Ubuntu\home\xpdlqj\code\projectH
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-gui-exe.ps1
```

- 증상:
  - 소스에서는 고친 동작인데 EXE 화면만 예전 상태
  - direct CLI/controller는 정상인데 EXE만 watcher나 카드 상태가 다름
  - `Active profile is missing` 같은 옛 문구가 EXE에서만 반복됨

## 8. watcher가 latest `/work`를 실제로 볼 수 있는지 확인
```bash
ls -t work/4/9 | head -n 5
sed -n '1,200p' .pipeline/claude_handoff.md
tail -n 120 .pipeline/logs/experimental/watcher.log
```

- 구현 라운드가 끝났으면 Claude는 `/work` closeout을 남겨야 합니다.
- watcher/Codex verify는 latest `/work`를 기준으로 움직입니다.
- `.pipeline`은 rolling slot일 뿐 `/work`를 대체하지 않습니다.

## 9. Claude가 막혔을 때 operator 선택지로 멈췄는지 확인
정상 경로:
- Claude는 `STATUS: implement` handoff만 구현
- 막히면 pane-local `STATUS: implement_blocked`
- watcher가 Codex triage로 자동 전달

비정상 경로:
- Claude가 operator에게 “다음 중 하나 선택”을 직접 요청
- `/work` 없이 구현 완료처럼만 말함
- 이미 끝난 handoff를 다시 잡고 멈춤

## 10. 메인 UI 해석
- `초안 지원 수준`: 현재 form/preview의 support truth
- `실행 프로필`: 현재 runtime active profile truth
- `설정 상태: 적용 완료`만으로 runtime 준비가 보장되지는 않습니다.
- runtime truth는 결국 `.pipeline/config/agent_profile.json` 존재와 direct CLI start 결과로 확인합니다.

## 11. 가장 흔한 판정

### A. `.pipeline/config/agent_profile.json`이 없다
- 원인: active profile materialization 실패 또는 stale UI
- 조치:
  - 최신 GUI/EXE로 다시 실행
  - setup `미리보기 생성 -> 적용` 재실행
  - 다시 2번, 4번 체크

### B. active profile은 있는데 start만 실패한다
- 원인: start path/session/path 해석 mismatch 가능성
- 조치:
  - direct CLI와 GUI의 project root 비교
  - session name, stale tmux, stale controller 확인

### C. Claude는 끝난 것 같은데 Codex verify가 안 돈다
- 원인: `/work` closeout 없음, 또는 watcher가 메타 note를 latest `/work`로 오인
- 조치:
  - latest `/work` 파일 확인
  - watcher 재시작 후 로그 재확인

### D. GUI는 초록인데 CLI는 차단된다
- 원인: stale GUI/EXE 또는 stale controller
- 조치:
  - Desktop exe 교체
  - `dist/pipeline-gui.exe`와 Desktop exe hash 비교
  - `.pipeline/gui-runtime/_data/` staged runtime drift 확인
  - GUI 완전 종료 후 재실행
  - 8780 stale controller 확인

### E. WSL `python3 pipeline-gui.py`는 정상인데 EXE만 죽는다
- 원인: EXE build snapshot drift 또는 safe-copy staging 누락 가능성이 가장 큼
- 조치:
  - `.pipeline/config`, `.pipeline/setup` 정리보다 EXE rebuild를 먼저 수행
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-gui-exe.ps1`
  - Desktop exe와 `dist/pipeline-gui.exe` hash가 같은지 재확인
  - 그래도 실패하면 EXE 에러 메시지의 `ModuleNotFoundError` 대상 패키지를 기준으로 staging 목록을 점검

## 12. 재시작 기본 명령
```bash
bash stop-pipeline.sh
bash -l start-pipeline.sh . --mode experimental --no-attach --session aip-projectH
```

## 13. 종료 조건
- `.pipeline/config/agent_profile.json`이 존재함
- direct CLI start가 `active profile missing`에서 더 이상 막히지 않음
- GUI의 `실행 프로필`이 direct CLI truth와 일치함
- 실제 실행 EXE와 `dist/pipeline-gui.exe`가 같은 빌드임
- Claude 구현 후 latest `/work`가 생기고 watcher가 Codex verify로 이어받음
