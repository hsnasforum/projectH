#!/bin/bash
# ============================================================
# build-gui-exe.sh — pipeline-gui.py를 Windows exe로 패키징
# ============================================================
#
# 사전 조건:
#   - Windows exe: Windows Python/PowerShell에서 pyinstaller 설치
#   - WSL/Linux 빌드: venv 안에서 pyinstaller 설치
#
# 실행:
#   bash scripts/build-gui-exe.sh
#
# 결과:
#   dist/pipeline-gui.exe  (Windows Python으로 빌드 시)
#   dist/pipeline-gui      (WSL 안에서 빌드 시, Linux only)
#
# 주의:
#   이 exe는 독립 실행형 앱이 아닙니다.
#   WSL + WSLg + tmux + agent CLI가 설치된 환경에서만 동작합니다.
#   exe는 "Windows에서 더블클릭으로 WSL GUI를 여는 wrapper"입니다.
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Pipeline GUI exe builder"
echo "========================"
echo "Project: $PROJECT_ROOT"
echo ""

PYINSTALLER_CMD=()
TKINTER_CHECK_CMD=()

if python3 -m PyInstaller --version &>/dev/null; then
    PYINSTALLER_CMD=(python3 -m PyInstaller)
    TKINTER_CHECK_CMD=(python3 -c "import tkinter")
elif python -m PyInstaller --version &>/dev/null; then
    PYINSTALLER_CMD=(python -m PyInstaller)
    TKINTER_CHECK_CMD=(python -c "import tkinter")
elif py -3 -m PyInstaller --version &>/dev/null; then
    PYINSTALLER_CMD=(py -3 -m PyInstaller)
    TKINTER_CHECK_CMD=(py -3 -c "import tkinter")
elif command -v pyinstaller &>/dev/null; then
    PYINSTALLER_CMD=(pyinstaller)
    if command -v python3 &>/dev/null; then
        TKINTER_CHECK_CMD=(python3 -c "import tkinter")
    elif command -v python &>/dev/null; then
        TKINTER_CHECK_CMD=(python -c "import tkinter")
    fi
else
    echo "[ERROR] 현재 bash 환경에서 PyInstaller를 찾지 못했습니다."
    echo "        Windows PowerShell에서 설치한 pyinstaller는 WSL/bash에서 보이지 않을 수 있습니다."
    echo "        - PowerShell에서 직접 빌드: scripts/PACKAGING.md 방법 B"
    echo "        - bash/WSL에서 빌드: python3 -m venv .venv-build && . .venv-build/bin/activate && python -m pip install pyinstaller"
    exit 1
fi

# tkinter 확인
if [ "${#TKINTER_CHECK_CMD[@]}" -gt 0 ]; then
    "${TKINTER_CHECK_CMD[@]}" 2>/dev/null || {
        echo "[ERROR] 현재 빌드 Python 환경에서 tkinter를 import하지 못했습니다."
        echo "        - WSL/bash 빌드: sudo apt install python3-tk"
        echo "        - Windows Python 빌드: tkinter 포함 Python 사용"
        exit 1
    }
fi

# 번들에 포함할 런타임 자산 확인
# 형식: "label|source|dest"
ASSET_SPECS=(
    "start-pipeline.sh|start-pipeline.sh|_data"
    "stop-pipeline.sh|stop-pipeline.sh|_data"
    "watcher_core.py|watcher_core.py|_data"
    "token_usage_shared.py|pipeline_gui/token_usage_shared.py|_data"
    "token_dashboard_shared.py|pipeline_gui/token_dashboard_shared.py|_data"
    "agent_manifest.schema.json|schemas/agent_manifest.schema.json|_data/schemas"
    "job_state.schema.json|schemas/job_state.schema.json|_data/schemas"
    "token-runtime|_data|_data"
    ".pipeline/README.md|.pipeline/README.md|_data/.pipeline"
)

echo "Checking bundled assets..."
MISSING=0
for spec in "${ASSET_SPECS[@]}"; do
    IFS='|' read -r label source dest <<< "$spec"
    if [ ! -e "$PROJECT_ROOT/$source" ]; then
        echo "  [WARN] Missing: $source"
        MISSING=1
    else
        echo "  [OK]   $label -> $dest"
    fi
done

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "[WARN] 일부 자산이 없습니다. 빌드를 계속하지만 Setup에서 경고가 뜰 수 있습니다."
    echo ""
fi

echo ""
echo "Building exe..."
echo ""

cd "$PROJECT_ROOT"

# --add-data로 런타임 자산을 _data/ 아래에 포함
# PyInstaller에서 : 는 Linux/Mac, ; 는 Windows 구분자
SEP=":"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    SEP=";"
fi

ADD_DATA_ARGS=()
for spec in "${ASSET_SPECS[@]}"; do
    IFS='|' read -r _label source dest <<< "$spec"
    if [ -e "$PROJECT_ROOT/$source" ]; then
        ADD_DATA_ARGS+=(--add-data "${source}${SEP}${dest}")
    fi
done

"${PYINSTALLER_CMD[@]}" \
    --onefile \
    --noconsole \
    --name "pipeline-gui" \
    --clean \
    --paths "$PROJECT_ROOT" \
    "${ADD_DATA_ARGS[@]}" \
    pipeline-gui.py

echo ""
echo "Build complete."
echo "Output: $PROJECT_ROOT/dist/pipeline-gui"
echo ""
echo "번들된 자산:"
for spec in "${ASSET_SPECS[@]}"; do
    IFS='|' read -r label source dest <<< "$spec"
    if [ -e "$PROJECT_ROOT/$source" ]; then
        if [ "$dest" = "." ]; then
            echo "  $(basename "$source")/"
        else
            echo "  $dest/$(basename "$source")"
        fi
    fi
done
echo ""
echo "사용법:"
echo "  1. dist/pipeline-gui.exe를 Windows 로컬 경로에 복사"
echo "  2. 더블클릭으로 실행"
echo "  3. Browse…로 WSL project path 선택 → Apply → Start"
echo ""
echo "사전 조건 (exe에 포함되지 않음):"
echo "  - WSL2 + WSLg (Windows 11)"
echo "  - WSL 내부: python3, python3-tk, tmux"
echo "  - WSL 내부: claude, codex, gemini CLI"
echo "  - WSL 내부: target project repo (git clone)"
