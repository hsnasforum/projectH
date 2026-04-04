#!/bin/bash
# ============================================================
# build-gui-exe.sh — pipeline-gui.py를 Windows exe로 패키징
# ============================================================
#
# 사전 조건:
#   pip install pyinstaller   (Windows Python 또는 WSL 안에서)
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

# PyInstaller 확인
if ! command -v pyinstaller &>/dev/null; then
    echo "[ERROR] PyInstaller가 설치되어 있지 않습니다."
    echo "        pip install pyinstaller"
    exit 1
fi

# tkinter 확인
python3 -c "import tkinter" 2>/dev/null || {
    echo "[ERROR] python3-tk가 설치되어 있지 않습니다."
    echo "        sudo apt install python3-tk"
    exit 1
}

# 번들에 포함할 런타임 자산 확인
ASSETS=(
    "start-pipeline.sh"
    "stop-pipeline.sh"
    "watcher_core.py"
    "schemas/agent_manifest.schema.json"
    "schemas/job_state.schema.json"
)

echo "Checking bundled assets..."
MISSING=0
for asset in "${ASSETS[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$asset" ]; then
        echo "  [WARN] Missing: $asset"
        MISSING=1
    else
        echo "  [OK]   $asset"
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

ADD_DATA_ARGS=""
for asset in "${ASSETS[@]}"; do
    if [ -f "$PROJECT_ROOT/$asset" ]; then
        # 대상 경로: _data/<원래_경로>
        DEST_DIR="_data/$(dirname "$asset")"
        ADD_DATA_ARGS="$ADD_DATA_ARGS --add-data ${asset}${SEP}${DEST_DIR}"
    fi
done

# .pipeline/README.md도 포함 (있으면)
if [ -f "$PROJECT_ROOT/.pipeline/README.md" ]; then
    ADD_DATA_ARGS="$ADD_DATA_ARGS --add-data .pipeline/README.md${SEP}_data/.pipeline"
fi

pyinstaller \
    --onefile \
    --noconsole \
    --name "pipeline-gui" \
    --clean \
    $ADD_DATA_ARGS \
    pipeline-gui.py

echo ""
echo "Build complete."
echo "Output: $PROJECT_ROOT/dist/pipeline-gui"
echo ""
echo "번들된 자산:"
for asset in "${ASSETS[@]}"; do
    if [ -f "$PROJECT_ROOT/$asset" ]; then
        echo "  _data/$asset"
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
