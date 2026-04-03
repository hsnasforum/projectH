#!/bin/bash
# ============================================================
# build-gui-exe.sh — pipeline-gui.py를 Windows exe로 패키징
# ============================================================
#
# 사전 조건:
#   pip install pyinstaller   (WSL 안에서)
#
# 실행:
#   bash scripts/build-gui-exe.sh
#
# 결과:
#   dist/pipeline-gui.exe
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

echo "Building exe..."
echo ""

cd "$PROJECT_ROOT"

pyinstaller \
    --onefile \
    --noconsole \
    --name "pipeline-gui" \
    --clean \
    pipeline-gui.py

echo ""
echo "Build complete."
echo "Output: $PROJECT_ROOT/dist/pipeline-gui.exe"
echo ""
echo "사용법:"
echo "  1. dist/pipeline-gui.exe를 Windows 로컬 경로에 복사"
echo "  2. 더블클릭으로 실행"
echo ""
echo "사전 조건 (exe에 포함되지 않음):"
echo "  - WSL2 + WSLg (Windows 11)"
echo "  - WSL 내부: python3, python3-tk, tmux"
echo "  - WSL 내부: claude, codex, gemini CLI"
echo "  - WSL 내부: projectH repo + start-pipeline.sh"
